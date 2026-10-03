import pygame

from bullet import Bullet
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, SHIP_MIN_Y, FPS, GUN_LAYOUTS,
                      SHIPS, compute_stats)


class PlayerShip:
    """Корабль игрока в игровом мире (только логика, без отрисовки)."""

    def __init__(self, index, loadout, n_players=1):
        self.index = index
        self.connected = True
        self.spawn_x = SCREEN_WIDTH * (index + 1) / (n_players + 1)
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.x = self.y = 0.0

        self.hp = self.max_hp = 1
        self.lives = self.max_lives = 0
        self.apply_loadout(loadout)
        self.hp = self.max_hp

        self.effects = {}    # временные эффекты из контейнеров: имя -> кадров осталось
        self.temp_weapon = None
        self.temp_cooldown = 0
        self.alive = True
        self.invuln = 90     # кадры неуязвимости после появления
        self.grace = 0       # короткая защита от повторного урона
        self.cooldown = 0
        self.score = 0
        self.coins = 0
        self.kills = 0
        self.respawn()

    def apply_loadout(self, loadout):
        """Применяет корпус, улучшения, оружие и снаряды.
        Можно вызывать посреди игры (покупки между уровнями, смена оружия)."""
        stats = compute_stats(loadout)
        hp_ratio = self.hp / self.max_hp
        self.loadout = loadout
        self.owned_weapons = set(loadout.get("weapons", [])) | {stats["weapon"]}
        self.owned_ammo = set(loadout.get("ammos", [])) | {stats["ammo"]}
        self.ship = stats["ship"]
        self.weapon = stats["weapon"]
        self.ammo = stats["ammo"]
        self.armor = stats["armor"]
        self.guns = stats["guns"]
        self.damage_mult = stats["damage_mult"]
        self.fire_cooldown = stats["cooldown"]
        self.speed = stats["speed"]
        self.regen = stats["regen"] / FPS
        self.max_hp = stats["max_hp"]
        self.hp = max(1.0, hp_ratio * self.max_hp)
        # Купленные жизни сразу добавляются
        self.lives += stats["lives"] - self.max_lives
        self.max_lives = stats["lives"]
        center = self.rect.center
        self.rect = pygame.Rect(0, 0, *SHIPS[self.ship]["size"])
        self.rect.center = center

    def _switch(self, weapon, ammo):
        """Смена оружия (E) и снарядов (Q) — только на купленные."""
        if weapon == self.weapon and ammo == self.ammo:
            return
        if weapon not in self.owned_weapons:
            weapon = self.weapon
        if ammo not in self.owned_ammo:
            ammo = self.ammo
        if (weapon, ammo) != (self.weapon, self.ammo):
            self.apply_loadout(dict(self.loadout, weapon=weapon, ammo=ammo))

    def grant_weapon(self, weapon, frames):
        """Трофейное оружие из контейнера на время (даже если оно не куплено)."""
        self.temp_weapon = weapon
        self.temp_cooldown = compute_stats(dict(self.loadout, weapon=weapon))["cooldown"]
        self.effects["weapon"] = frames

    @property
    def current_weapon(self):
        return self.temp_weapon or self.weapon

    def _tick_effects(self):
        for name in list(self.effects):
            self.effects[name] -= 1
            if self.effects[name] <= 0:
                del self.effects[name]
                if name == "weapon":
                    self.temp_weapon = None
        if "radiation" in self.effects:
            # Радиация медленно разъедает корпус, но не добивает
            self.hp = max(1.0, self.hp - 5 / FPS)

    def respawn(self):
        """Ставит корабль в стартовую точку у нижнего края экрана."""
        self.x = float(self.spawn_x)
        self.y = float(SCREEN_HEIGHT - self.rect.height / 2 - 10)
        self.rect.center = (round(self.x), round(self.y))

    @property
    def hitbox(self):
        return self.rect.inflate(-self.rect.width // 3, -self.rect.height // 3)

    def update(self, inp):
        """Движение и стрельба. Возвращает список новых снарядов."""
        if self.invuln > 0:
            self.invuln -= 1
        if self.grace > 0:
            self.grace -= 1
        if self.cooldown > 0:
            self.cooldown -= 1
        self.hp = min(self.max_hp, self.hp + self.regen)
        self._tick_effects()
        self._switch(inp.get("w", self.weapon), inp.get("a", self.ammo))

        dx = inp.get("r", 0) - inp.get("l", 0)
        dy = inp.get("d", 0) - inp.get("u", 0)
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        if "virus" in self.effects:
            dx, dy = -dx, -dy          # «вирус» путает управление
        speed = self.speed * (0.5 if "corrosion" in self.effects else 1)
        half_w, half_h = self.rect.width / 2, self.rect.height / 2
        self.x = min(max(self.x + dx * speed, half_w), SCREEN_WIDTH - half_w)
        self.y = min(max(self.y + dy * speed, SHIP_MIN_Y + half_h),
                     SCREEN_HEIGHT - half_h - 4)
        self.rect.center = (round(self.x), round(self.y))

        if inp.get("f") and self.cooldown <= 0 and "jam" not in self.effects:
            cooldown = self.temp_cooldown if self.temp_weapon else self.fire_cooldown
            if "overdrive" in self.effects:
                cooldown = max(2, cooldown // 2)
            self.cooldown = cooldown
            damage = self.damage_mult * (1.5 if "power" in self.effects else 1)
            return [Bullet(self.index, self.current_weapon, self.ammo, self.x + offset,
                           self.rect.top + 8, angle, damage)
                    for offset, angle in GUN_LAYOUTS[self.guns]]
        return []
