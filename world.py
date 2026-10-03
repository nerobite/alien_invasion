import math
import random

from alien import Alien
from bullet import EnemyBullet
from debris import Wreck, Pickup
from meteor import Meteor
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, FORMATION_TOP, SLOT_W, SLOT_H,
                      FLEET_DROP, PLAYER_COLORS, WORLDS, LEVELS_PER_WORLD,
                      DIFFICULTIES, AMMO_ORDER, ALIEN_TYPES, BOSS_ATTACKS, WRECKS, WRECKS_PER_10S, PICKUPS,
                      WEAPON_ORDER, WEAPONS, world_of_level)
from ship import PlayerShip

WAVE_CLEAR_DELAY = 90     # кадров между последним сбитым врагом и перерывом
GAME_OVER_DELAY = 120     # кадров между гибелью последнего корабля и концом игры


class GameWorld:
    """Вся игровая логика. Не рисует и не читает клавиатуру:
    получает нажатия игроков в step() и отдает состояние в snapshot().
    Поэтому один и тот же мир работает и в одиночной, и в сетевой игре.

    После каждой отбитой волны мир встает на перерыв (intermission = True):
    в это время можно зайти в магазин. Следующий уровень начинает next_level().
    """

    def __init__(self, loadouts, difficulty="normal", start_world=0):
        n = len(loadouts)
        self.players = [PlayerShip(i, lo, n) for i, lo in enumerate(loadouts)]
        self.difficulty = difficulty if difficulty in DIFFICULTIES else "normal"
        self.diff = DIFFICULTIES[self.difficulty]
        self.level = start_world * LEVELS_PER_WORLD + 1
        self.aliens = []
        self.bullets = []
        self.enemy_bullets = []
        self.meteors = []
        self.wrecks = []
        self.pickups = []
        self.events = []          # эффекты для отрисовки (взрывы, монеты...)
        self.fleet_direction = 1
        self.banner = ""
        self.banner_timer = 0
        self.clear_timer = 0
        self.over_timer = 0
        self.intermission = False
        self.game_over = False
        self._start_wave()

    @property
    def score(self):
        """Общий счет команды."""
        return sum(p.score for p in self.players)

    @property
    def world_index(self):
        return world_of_level(self.level)

    @property
    def world(self):
        return WORLDS[self.world_index]

    @property
    def level_in_world(self):
        return (self.level - 1) % LEVELS_PER_WORLD + 1

    @property
    def is_boss_level(self):
        return self.level_in_world == LEVELS_PER_WORLD

    # ------------------------------------------------------------ волны
    def _hp_scale(self):
        """Пришельцы крепче с каждым уровнем, в игре вдвоем и на высокой сложности."""
        return ((1 + 0.1 * (self.level - 1)) * (1 + 0.6 * (len(self.players) - 1))
                * self.diff["hp"])

    def _new_alien(self, kind, x, y, hp_scale=None):
        return Alien(kind, x, y, self.level, hp_scale or self._hp_scale(),
                     self.diff["coins"], self.diff["fire"])

    def _show_banner(self, text, frames=150):
        self.banner = text
        self.banner_timer = frames

    def _start_wave(self):
        self.fleet_direction = 1
        self.enemy_bullets.clear()
        top = FORMATION_TOP
        title = f"Мир {self.world_index + 1}: {self.world['name']} — уровень {self.level_in_world}"
        if self.is_boss_level:
            boss_scale = ((3 + 0.7 * self.level) * (1 + 0.6 * (len(self.players) - 1))
                          * self.diff["hp"])
            self.aliens.append(self._new_alien(self.world["boss"], SCREEN_WIDTH / 2, -100,
                                               boss_scale))
            rows, cols, top = 2, 10, FORMATION_TOP + 200
            self._show_banner(title + ". БОСС!", 180)
        else:
            rows = min(3 + (self.level - 1) // 6, 6)
            cols = min(8 + (self.level - 1) // 5, 12)
            self._show_banner(title)

        start_x = (SCREEN_WIDTH - cols * SLOT_W) / 2 + SLOT_W / 2
        for row in range(rows):
            for col in range(cols):
                self.aliens.append(self._new_alien(self._pick_kind(row), start_x + col * SLOT_W,
                                                   top + row * SLOT_H))

    def _pick_kind(self, row):
        """Случайный тип пришельца из набора текущего мира.
        На первых уровнях мира доступны только первые типы из списка."""
        enemies = list(self.world["enemies"].items())
        allowed = enemies[:min(len(enemies), 2 + (self.level_in_world - 1) // 2)]
        if self.level > LEVELS_PER_WORLD * len(WORLDS):
            allowed = enemies   # второй круг миров — сразу все враги
        kinds = [k for k, _ in allowed]
        weights = [w * (3 if row == 0 and k in ("tank", "bomber", "twin") else 1) for k, w in allowed]
        return random.choices(kinds, weights)[0]

    def spawn_divers(self, source, kind, count):
        for i in range(count):
            alien = self._new_alien(kind, source.x + (i - (count - 1) / 2) * 50, source.y + 30)
            alien.state = "dive"
            if kind == "mini":
                alien.dive_speed *= 0.7
                alien.vx = (i - (count - 1) / 2) * 2
            self.aliens.append(alien)

    def next_level(self):
        """Конец перерыва: следующий уровень."""
        if not self.intermission:
            return
        self.intermission = False
        self.level += 1
        # Погибший напарник возвращается в бой с одной жизнью
        for player in self.players:
            if not player.alive and player.connected:
                player.alive = True
                player.lives = 1
                player.hp = player.max_hp
                player.invuln = 120
                player.respawn()
            elif player.alive:
                player.invuln = 60
                player.respawn()
        self.over_timer = 0
        self._start_wave()

    # ------------------------------------------------------------ шаг игры
    def step(self, inputs):
        """Один кадр игры. inputs — список нажатий для каждого игрока."""
        if self.game_over or self.intermission:
            return
        if self.banner_timer:
            self.banner_timer -= 1

        for player, inp in zip(self.players, inputs):
            if player.alive:
                self.bullets.extend(player.update(inp))

        self._update_aliens()
        self._update_meteors()
        self._update_debris()
        self._update_bullets()
        self._update_enemy_bullets()
        self._check_rams()
        self._check_wave()

        if not any(p.alive for p in self.players):
            self.over_timer += 1
            if self.over_timer >= GAME_OVER_DELAY:
                self.game_over = True

    def _update_aliens(self):
        formation = [a for a in self.aliens if a.state == "formation"]
        speed = min(0.8 + 0.05 * (self.level - 1), 3.2) * self.diff["speed"]
        for alien in formation:
            alien.x += speed * self.fleet_direction * alien.speed_factor
        # Флот достиг края — спускается и разворачивается
        if any(a.x + a.rect.width / 2 >= SCREEN_WIDTH - 8 and self.fleet_direction > 0
               or a.x - a.rect.width / 2 <= 8 and self.fleet_direction < 0
               for a in formation):
            self.fleet_direction *= -1
            for alien in formation:
                alien.y += FLEET_DROP

        for alien in list(self.aliens):
            alien.update(self)
            # Пришелец из строя добрался до низа — урон всем игрокам
            if alien.state == "formation" and alien.rect.bottom >= SCREEN_HEIGHT:
                alien.dead = True
                self._explosion(alien)
                for player in self.players:
                    self._hurt_player(player, 25, ignore_grace=True)
        self.aliens = [a for a in self.aliens if not a.dead]

    def _update_meteors(self):
        # Новые метеориты: примерно world['meteors'] штук за 10 секунд
        if random.random() < self.world["meteors"] / 600 and len(self.meteors) < 8:
            self.meteors.append(Meteor.random_spawn(
                self.diff["hp"] * (1 + 0.05 * (self.level - 1)), self.diff["speed"]))

        rects = [a.rect for a in self.aliens]
        for meteor in self.meteors:
            meteor.update()
            # Метеорит сносит пришельцев (монеты за это никому не достаются)
            for i in meteor.rect.collidelistall(rects):
                alien = self.aliens[i]
                if alien.dead or alien.id in meteor.hit_ids or not meteor.collides(alien.rect):
                    continue
                meteor.hit_ids.add(alien.id)
                damage = alien.max_hp * 0.08 if alien.is_boss else alien.max_hp
                self._damage_alien(alien, damage, None)
                meteor.hp -= 2 + 2 * meteor.big
                if meteor.hp <= 0:
                    self._break_meteor(meteor, None)
                    break
        self.aliens = [a for a in self.aliens if not a.dead]
        self.meteors = [m for m in self.meteors if not m.dead and not m.off_screen()]

    def _update_debris(self):
        """Обломки дрейфуют, контейнеры падают и подбираются кораблями."""
        if random.random() < WRECKS_PER_10S / 600 and len(self.wrecks) < 3:
            self.wrecks.append(Wreck(random.choice(list(WRECKS)),
                                     self.diff["hp"] * (1 + 0.05 * (self.level - 1))))
        for wreck in self.wrecks:
            wreck.update()
        for pickup in self.pickups:
            pickup.update()
            for player in self.players:
                if player.alive and player.rect.colliderect(pickup.rect):
                    pickup.dead = True
                    self._open_pickup(player, pickup)
                    break
        self.wrecks = [w for w in self.wrecks if not w.dead and not w.off_screen()]
        self.pickups = [p for p in self.pickups if not p.dead and not p.off_screen()]

    def _damage_wreck(self, wreck, damage):
        wreck.hp -= damage
        wreck.flash = 4
        if wreck.hp <= 0:
            self._break_wreck(wreck)

    def _break_wreck(self, wreck):
        if wreck.dead:
            return
        wreck.dead = True
        self.events.append(["x", wreck.rect.centerx, wreck.rect.centery, 170, 170, 180, 1])
        self.pickups.append(Pickup(wreck.x, wreck.y))

    def _open_pickup(self, player, pickup):
        """Сюрприз из контейнера: полезный или вредный эффект."""
        names = list(PICKUPS)
        effect = random.choices(names, [PICKUPS[n]["weight"] for n in names])[0]
        info = PICKUPS[effect]
        text = info["name"]
        if effect == "coins":
            amount = max(1, round(random.randint(10, 30) * self.diff["coins"]))
            player.coins += amount
            text = f"+{amount} монет"
        elif effect == "repair":
            player.hp = min(player.max_hp, player.hp + 0.4 * player.max_hp)
        elif effect == "life":
            player.lives += 1
        elif effect == "trap":
            player.effects.pop("shield", None)
            self._hurt_player(player, 30 * self.diff["damage"], ignore_grace=True)
        elif effect == "weapon":
            weapon = random.choice([w for w in WEAPON_ORDER if w != player.weapon])
            player.grant_weapon(weapon, info["duration"])
            text = f"Трофей: {WEAPONS[weapon]['name']}"
        else:
            player.effects[effect] = info["duration"]
        self.events.append(["pk", round(pickup.x), round(pickup.y), text, int(info["good"]),
                            player.index])

    def _update_bullets(self):
        targets = self.aliens + self.meteors + self.wrecks
        rects = [t.rect for t in targets]
        remaining = []
        for bullet in self.bullets:
            bullet.update(self.aliens)
            if bullet.off_screen():
                continue
            consumed = False
            for i in bullet.rect.collidelistall(rects):
                target = targets[i]
                if target.dead or target.id in bullet.hit_ids:
                    continue
                if isinstance(target, Meteor):
                    self._damage_meteor(target, bullet.damage, bullet.owner)
                elif isinstance(target, Wreck):
                    self._damage_wreck(target, bullet.damage)
                else:
                    self._damage_alien(target, bullet.damage, bullet.owner)
                    if bullet.slow:
                        target.slowed = bullet.slow
                if bullet.splash:
                    self._splash(bullet, target)
                if bullet.pierce > 0:
                    bullet.pierce -= 1
                    bullet.hit_ids.add(target.id)
                else:
                    consumed = True
                    break
            if not consumed:
                remaining.append(bullet)
        self.bullets = remaining
        self.aliens = [a for a in self.aliens if not a.dead]
        self.meteors = [m for m in self.meteors if not m.dead]
        self.wrecks = [w for w in self.wrecks if not w.dead]

    def _splash(self, bullet, direct_hit):
        self.events.append(["s", round(bullet.x), round(bullet.y), bullet.splash])
        for alien in self.aliens:
            if alien is direct_hit or alien.dead:
                continue
            if math.hypot(alien.x - bullet.x, alien.y - bullet.y) <= bullet.splash:
                self._damage_alien(alien, bullet.damage * 0.6, bullet.owner)
                if bullet.slow:
                    alien.slowed = bullet.slow

    def _reward(self, owner, target):
        if owner is None:
            return
        player = self.players[owner]
        player.score += target.points
        player.coins += target.coins
        self.events.append(["c", target.rect.centerx, target.rect.centery,
                            target.coins, owner])

    def _damage_alien(self, alien, damage, owner):
        """owner — индекс игрока, None — пришелец разбит метеоритом."""
        if alien.dead:
            return
        alien.hp -= damage
        alien.flash = 4
        if alien.hp > 0:
            return
        alien.dead = True
        self._explosion(alien)
        if owner is not None:
            self.players[owner].kills += 1
        self._reward(owner, alien)
        if alien.kind == "splitter":
            self.spawn_divers(alien, "mini", 2)

    def _damage_meteor(self, meteor, damage, owner):
        meteor.hp -= damage
        meteor.flash = 4
        if meteor.hp <= 0:
            self._break_meteor(meteor, owner)

    def _break_meteor(self, meteor, owner):
        if meteor.dead:
            return
        meteor.dead = True
        self.events.append(["x", meteor.rect.centerx, meteor.rect.centery,
                            150, 120, 100, 2 if meteor.big else 1])
        if owner is not None:
            meteor.coins = max(1, round(meteor.coins * self.diff["coins"]))
            self._reward(owner, meteor)
        if meteor.big:
            self.meteors.extend(meteor.fragments())

    def _explosion(self, alien):
        size = 3 if alien.is_boss else (2 if alien.rect.width >= 55 else 1)
        color = (255, 120, 60) if alien.is_boss else (255, 200, 90)
        self.events.append(["x", alien.rect.centerx, alien.rect.centery, *color, size])

    def _update_enemy_bullets(self):
        remaining = []
        for bullet in self.enemy_bullets:
            bullet.update()
            if bullet.off_screen():
                continue
            hit = False
            for player in self.players:
                if player.alive and player.invuln <= 0 and player.hitbox.colliderect(bullet.rect):
                    self._hurt_player(player, bullet.damage, ignore_grace=True)
                    hit = True
                    break
            if not hit:
                remaining.append(bullet)
        self.enemy_bullets = remaining

    def _check_rams(self):
        """Столкновения пришельцев и метеоритов с кораблями."""
        for player in self.players:
            if not player.alive or player.invuln > 0:
                continue
            hitbox = player.hitbox
            for alien in self.aliens:
                if alien.dead or not hitbox.colliderect(alien.rect):
                    continue
                self._hurt_player(player, alien.ram_damage * self.diff["damage"])
                if not alien.is_boss:
                    alien.dead = True
                    self._explosion(alien)
            for meteor in self.meteors:
                if not meteor.dead and meteor.collides(hitbox):
                    self._hurt_player(player, meteor.damage * self.diff["damage"],
                                      ignore_grace=True)
                    meteor.big = 0   # осколков от тарана не будет
                    self._break_meteor(meteor, None)
            for wreck in self.wrecks:
                if not wreck.dead and hitbox.colliderect(wreck.rect):
                    self._hurt_player(player, wreck.damage * self.diff["damage"])
                    self._break_wreck(wreck)
        self.aliens = [a for a in self.aliens if not a.dead]
        self.meteors = [m for m in self.meteors if not m.dead]
        self.wrecks = [w for w in self.wrecks if not w.dead]

    def _check_wave(self):
        if self.aliens or self.game_over:
            return
        if self.clear_timer == 0:
            self.clear_timer = WAVE_CLEAR_DELAY
            bonus = max(1, round((5 + 2 * self.level) * self.diff["coins"]))
            for player in self.players:
                if player.alive:
                    player.coins += bonus
                    self.events.append(["c", player.rect.centerx, player.rect.top,
                                        bonus, player.index])
            self.enemy_bullets.clear()
            self._show_banner(f"Уровень {self.level} пройден!", WAVE_CLEAR_DELAY)
            return
        self.clear_timer -= 1
        if self.clear_timer == 0:
            # Перерыв: экран очищается, можно заглянуть в магазин
            self.intermission = True
            self.bullets.clear()
            self.meteors.clear()
            self.wrecks.clear()
            self.pickups.clear()
            self.banner_timer = 0

    # ------------------------------------------------------------ игроки
    def nearest_player(self, x, y):
        alive = [p for p in self.players if p.alive]
        return min(alive, default=None, key=lambda p: (p.x - x) ** 2 + (p.y - y) ** 2)

    def _hurt_player(self, player, amount, ignore_grace=False):
        if not player.alive or player.invuln > 0:
            return
        if player.grace > 0 and not ignore_grace:
            return
        if "shield" in player.effects:
            return
        damage = amount * (1 - player.armor)
        player.hp -= damage
        player.grace = 15
        self.events.append(["h", player.index, round(damage)])
        if player.hp > 0:
            return
        player.lives -= 1
        self.events.append(["X", player.rect.centerx, player.rect.centery,
                            *PLAYER_COLORS[player.index]])
        if player.lives > 0:
            player.hp = player.max_hp
            player.invuln = 150
            player.respawn()
        else:
            player.hp = 0
            player.alive = False

    def disconnect_player(self, index):
        """Игрок покинул сетевую игру: его корабль выбывает."""
        player = self.players[index]
        player.connected = False
        player.alive = False
        player.lives = 0
        player.hp = 0

    # ------------------------------------------------------------ огонь пришельцев
    def _power(self):
        return (1 + 0.035 * (self.level - 1)) * self.diff["damage"]

    def _shoot(self, x, y, angle, speed, damage, kind):
        self.enemy_bullets.append(EnemyBullet(x, y, speed * math.cos(angle),
                                              speed * math.sin(angle), damage, kind))

    def _aim(self, x, y):
        target = self.nearest_player(x, y)
        if target is None:
            return math.pi / 2   # прямо вниз
        return math.atan2(target.y - y, target.x - x)

    def alien_fire(self, alien):
        """Выстрел обычного пришельца по описанию gun из ALIEN_TYPES."""
        gun = ALIEN_TYPES[alien.kind].get("gun")
        if gun is None or len(self.enemy_bullets) >= 25 + self.level:
            return
        aim, kind, speed, damage = gun
        x, y = alien.rect.centerx, alien.rect.bottom
        angle = self._aim(x, y) if aim == "aim" else math.pi / 2
        self._shoot(x, y, angle, speed, damage * self._power(), kind)

    def boss_attack(self, boss):
        """Атаки босса по расписанию из BOSS_ATTACKS. С уровнем босс атакует чаще."""
        t = boss.timer - 120          # первые 2 секунды босс только влетает
        if t < 0 or len(self.enemy_bullets) > 70:
            return
        if boss.slowed and t % 2:
            return   # замедленный босс атакует реже
        power = self._power()
        speedup = max(0.6, 1 - 0.005 * (self.level - 1))
        x, y = boss.rect.centerx, boss.rect.bottom - 10
        for attack, period, offset, p in BOSS_ATTACKS[boss.kind]:
            period = max(20, int(period * speedup))
            phase = (t - offset) % period
            if attack == "burst":
                if phase % p["gap"] == 0 and phase // p["gap"] < p["n"]:
                    self._shoot(x, y, self._aim(x, y), p["speed"], p["dmg"] * power, p["kind"])
                continue
            if phase != 0:
                continue
            if attack == "spread":
                aim = self._aim(x, y)
                for i in range(p["n"]):
                    self._shoot(x, y, aim + (i - (p["n"] - 1) / 2) * p["step"], p["speed"],
                                p["dmg"] * power, p["kind"])
            elif attack == "ring":
                turn = t * p["spin"]
                for i in range(p["n"]):
                    self._shoot(boss.x, boss.y, turn + i * 2 * math.pi / p["n"], p["speed"],
                                p["dmg"] * power, p["kind"])
            elif attack == "bombs":
                for frac in p["points"]:
                    bx = boss.rect.left + boss.rect.width * frac
                    self._shoot(bx, boss.rect.bottom - 6, math.pi / 2, 2.8, p["dmg"] * power, "k")
            elif attack == "spawn":
                self.spawn_divers(boss, p["kind"], p["n"])

    # ------------------------------------------------------------ состояние
    def snapshot(self):
        """Компактное состояние мира для отрисовки и передачи по сети."""
        events, self.events = self.events, []
        return {
            "t": "s",
            "lvl": self.level,
            "w": self.world_index,
            "df": self.difficulty,
            "im": int(self.intermission),
            "go": self.game_over,
            "bn": self.banner if self.banner_timer > 0 else "",
            "p": [[p.rect.centerx, p.rect.centery, round(p.hp), p.max_hp, p.lives,
                   int(p.alive), p.invuln, p.score, p.coins, p.current_weapon, p.kills,
                   int(p.connected), p.ship, p.ammo, dict(p.effects), p.guns]
                  for p in self.players],
            "a": [[a.kind, a.rect.centerx, a.rect.centery,
                   round(max(a.hp, 0) / a.max_hp, 2), int(a.flash > 0) | (2 if a.slowed else 0)]
                  for a in self.aliens],
            "m": [[m.big, m.rect.centerx, m.rect.centery, int(m.angle), int(m.flash > 0)]
                  for m in self.meteors],
            "wr": [[w.variant, w.rect.centerx, w.rect.centery, int(w.angle), int(w.flash > 0)]
                   for w in self.wrecks],
            "pu": [[p.rect.centerx, p.rect.centery] for p in self.pickups],
            "b": [[b.weapon, round(b.x), round(b.y), round(b.vx, 1), round(b.vy, 1),
                   AMMO_ORDER.index(b.ammo)]
                  for b in self.bullets],
            "e": [[round(b.x), round(b.y), b.kind] for b in self.enemy_bullets],
            "ev": events,
        }
