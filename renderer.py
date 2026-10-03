import math
import random

import pygame

from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, ALIEN_TYPES, SHIPS, WEAPONS, AMMO,
                      AMMO_ORDER, METEORS, WRECKS, PICKUPS, WORLDS, DIFFICULTIES,
                      LEVELS_PER_WORLD, FPS, PLAYER_COLORS, PLAYER_NAMES)
from utils import resource_path, draw_text, draw_coin, silhouette, get_font

HUD_HEIGHT = 52


def load_image(name, size):
    """Загружает спрайт: у BMP черный фон становится прозрачным, PNG уже прозрачные."""
    image = pygame.image.load(resource_path("images/" + name))
    if name.endswith(".bmp"):
        image = image.convert()
        image.set_colorkey((0, 0, 0))
    image = image.convert_alpha()
    if image.get_size() != tuple(size):
        image = pygame.transform.smoothscale(image, size)
    return image


def make_nebula(world):
    """Фон мира: мягкие цветные облака туманности на темном небе."""
    rng = random.Random(world["name"])
    small = pygame.Surface((160, 90), pygame.SRCALPHA)
    small.fill(world["bg"] + (255,))
    for _ in range(14):
        color = rng.choice(world["nebula"])
        r = rng.randint(12, 34)
        blob = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            pygame.draw.circle(blob, color + (int(10 * (1 - i / r)) + 3,), (r, r), i)
        small.blit(blob, (rng.randint(-r, 160 - r), rng.randint(-r, 90 - r)))
    return pygame.transform.smoothscale(small, (SCREEN_WIDTH, SCREEN_HEIGHT)).convert()


class Renderer:
    """Рисует игровой мир по снимку состояния (GameWorld.snapshot()).

    Снимок одинаков для одиночной игры, хоста и клиента, поэтому
    все видят одну и ту же картинку.
    """

    def __init__(self):
        self.ship_images = {sid: load_image(info["image"], info["size"])
                            for sid, info in SHIPS.items()}
        self.life_icons = {sid: pygame.transform.smoothscale(img, (14, 18))
                           for sid, img in self.ship_images.items()}
        self._outlines = {}

        self.alien_images = {}
        self.alien_flash = {}
        self.alien_ice = {}
        for kind, info in ALIEN_TYPES.items():
            image = load_image(info["image"], info["size"])
            self.alien_images[kind] = image
            self.alien_flash[kind] = silhouette(image)
            ice = silhouette(image, (120, 200, 255))
            ice.set_alpha(130)
            self.alien_ice[kind] = ice

        # Повернутые кадры метеоритов (через каждые 10 градусов)
        self.meteor_frames = {}
        for big, info in METEORS.items():
            base = load_image(info["image"], (info["size"], info["size"]))
            self.meteor_frames[big] = [pygame.transform.rotate(base, a) for a in range(0, 360, 10)]
        self.meteor_flash = {big: silhouette(frames[0]) for big, frames in self.meteor_frames.items()}

        self.wreck_frames = {}
        for variant, info in WRECKS.items():
            base = load_image(info["image"], info["size"])
            self.wreck_frames[variant] = [pygame.transform.rotate(base, a) for a in range(0, 360, 10)]
        self.crate = load_image("crate.png", (30, 30))
        draw_text(self.crate, "?", 20, (60, 30, 0), (15, 15), "center", True)

        self.backgrounds = [make_nebula(world) for world in WORLDS]

        self.particles = []   # [x, y, vx, vy, life, max_life, color, size]
        self.floaters = []    # всплывающий текст: [x, y, text, color, life]
        self.rings = []       # ударные волны: [x, y, radius, life]
        self.damage_flash = 0
        self.frame = 0

    def draw_background(self, screen, world_index=0):
        screen.blit(self.backgrounds[world_index % len(self.backgrounds)], (0, 0))

    def ship_outline(self, ship, player_index):
        """Цветной контур корабля — чтобы в кооперативе различать игроков."""
        key = (ship, player_index)
        if key not in self._outlines:
            image = self.ship_images[ship]
            glow = silhouette(image, PLAYER_COLORS[player_index])
            w, h = image.get_size()
            self._outlines[key] = pygame.transform.smoothscale(glow, (w + 8, h + 8))
        return self._outlines[key]

    # ------------------------------------------------------------ эффекты
    def reset_effects(self):
        self.particles.clear()
        self.floaters.clear()
        self.rings.clear()
        self.damage_flash = 0

    def process_events(self, events, local_index):
        """Создает эффекты по событиям мира (вызывать один раз на событие)."""
        for ev in events:
            kind = ev[0]
            if kind == "x":
                _, x, y, r, g, b, size = ev
                self._burst(x, y, (r, g, b), 14 * size, 1.5 + size)
                if size >= 3:
                    self.rings.append([x, y, 160, 30])
            elif kind == "X":
                _, x, y, r, g, b = ev
                self._burst(x, y, (r, g, b), 50, 5)
                self._burst(x, y, (255, 255, 255), 20, 3)
            elif kind == "c":
                _, x, y, amount, owner = ev
                color = (255, 215, 60) if owner == local_index else (170, 150, 90)
                self.floaters.append([x, y, f"+{amount}", color, 50])
            elif kind == "s":
                _, x, y, radius = ev
                self.rings.append([x, y, radius, 14])
                self._burst(x, y, (255, 180, 60), 8, 3)
            elif kind == "pk":
                _, x, y, text, good, owner = ev
                color = (120, 255, 140) if good else (255, 110, 110)
                self.floaters.append([x, y - 20, text, color, 90])
                self._burst(x, y, color, 16, 3)
            elif kind == "h" and ev[1] == local_index:
                self.damage_flash = 12

    def _burst(self, x, y, color, count, power):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, power)
            life = random.randint(20, 45)
            self.particles.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                   life, life, color, random.randint(2, 4)])

    def _update_effects(self):
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.96
            p[3] *= 0.96
            p[4] -= 1
        self.particles = [p for p in self.particles if p[4] > 0]
        for f in self.floaters:
            f[1] -= 0.8
            f[4] -= 1
        self.floaters = [f for f in self.floaters if f[4] > 0]
        for r in self.rings:
            r[3] -= 1
        self.rings = [r for r in self.rings if r[3] > 0]
        if self.damage_flash:
            self.damage_flash -= 1

    # ------------------------------------------------------------ отрисовка
    def draw_world(self, screen, snap, local_index, high_score=None, hint=""):
        self.frame += 1
        self._update_effects()

        for big, x, y, angle, flash in snap["m"]:
            frames = self.meteor_frames[big]
            image = frames[(angle // 10) % len(frames)]
            screen.blit(image, image.get_rect(center=(x, y)))
            if flash:
                screen.blit(self.meteor_flash[big], self.meteor_flash[big].get_rect(center=(x, y)))
        for variant, x, y, angle, flash in snap["wr"]:
            frames = self.wreck_frames[variant]
            image = frames[(angle // 10) % len(frames)]
            rect = image.get_rect(center=(x, y))
            screen.blit(image, rect)
            if flash:
                pygame.draw.rect(screen, (255, 255, 255), rect.inflate(-rect.width // 2, -rect.height // 2), 2)
        bob = 3 * math.sin(self.frame * 0.15)
        for x, y in snap["pu"]:
            screen.blit(self.crate, self.crate.get_rect(center=(x, y + bob)))
        for kind, x, y, hp_frac, flags in snap["a"]:
            self._draw_alien(screen, kind, x, y, hp_frac, flags)
        for x, y, kind in snap["e"]:
            self._draw_enemy_bullet(screen, x, y, kind)
        for bullet in snap["b"]:
            self._draw_bullet(screen, *bullet)
        for index, player in enumerate(snap["p"]):
            self._draw_ship(screen, index, player, len(snap["p"]) > 1)

        for x, y, vx, vy, life, max_life, color, size in self.particles:
            k = life / max_life
            c = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            pygame.draw.circle(screen, c, (int(x), int(y)), size)
        for x, y, radius, life in self.rings:
            total = 30 if radius > 100 else 14
            r = int(radius * (1 - life / total)) + 4
            pygame.draw.circle(screen, (255, 200, 90), (x, y), r, 2)
        for x, y, text, color, life in self.floaters:
            draw_text(screen, text, 20, color, (x, int(y)), "center", bold=True)

        if self.damage_flash:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, self.damage_flash * 6))
            screen.blit(overlay, (0, 0))

        self._draw_hud(screen, snap, local_index, high_score)
        if local_index < len(snap["p"]):
            self._draw_effects(screen, snap["p"][local_index][14])
        if hint:
            draw_text(screen, hint, 16, (190, 190, 220), (SCREEN_WIDTH - 12, SCREEN_HEIGHT - 8),
                      "bottomright")
        if snap["bn"]:
            size = 48 if len(snap["bn"]) > 30 else 56
            draw_text(screen, snap["bn"], size, (0, 0, 0), (SCREEN_WIDTH // 2 + 3, 283), "center", True)
            draw_text(screen, snap["bn"], size, (255, 255, 255), (SCREEN_WIDTH // 2, 280), "center", True)

    @staticmethod
    def _draw_effects(screen, effects):
        """Плашки активных эффектов игрока внизу слева."""
        x = 12
        for name, frames in sorted(effects.items()):
            info = PICKUPS[name]
            color = (60, 160, 80) if info["good"] else (170, 50, 50)
            label = f"{info['name'].split(':')[0]} {frames // FPS + 1}с"
            width = get_font(16, True).size(label)[0] + 16
            chip = pygame.Rect(x, SCREEN_HEIGHT - 34, width, 26)
            pygame.draw.rect(screen, color, chip, border_radius=6)
            draw_text(screen, label, 16, (255, 255, 255), chip.center, "center", True)
            x += width + 8

    def _draw_alien(self, screen, kind, x, y, hp_frac, flags):
        image = self.alien_flash[kind] if flags & 1 else self.alien_images[kind]
        rect = image.get_rect(center=(x, y))
        screen.blit(image, rect)
        if flags & 2:
            screen.blit(self.alien_ice[kind], rect)
        if ALIEN_TYPES[kind].get("boss"):
            # Большая полоса здоровья босса вверху экрана
            bar = pygame.Rect(SCREEN_WIDTH // 2 - 250, HUD_HEIGHT + 10, 500, 14)
            pygame.draw.rect(screen, (60, 0, 0), bar)
            pygame.draw.rect(screen, (255, 60, 90),
                             (bar.x, bar.y, int(bar.width * hp_frac), bar.height))
            pygame.draw.rect(screen, (255, 255, 255), bar, 1)
            draw_text(screen, ALIEN_TYPES[kind]["name"], 16, (255, 255, 255), bar.center, "center", True)
        elif hp_frac < 1:
            bar = pygame.Rect(rect.x, rect.y - 6, rect.width, 3)
            pygame.draw.rect(screen, (80, 0, 0), bar)
            pygame.draw.rect(screen, (90, 255, 90), (bar.x, bar.y, int(bar.width * hp_frac), 3))

    @staticmethod
    def _draw_enemy_bullet(screen, x, y, kind):
        if kind == "b":
            pygame.draw.circle(screen, (120, 0, 120), (x, y), 9)
            pygame.draw.circle(screen, (255, 90, 255), (x, y), 6)
        elif kind == "s":
            pygame.draw.circle(screen, (0, 90, 120), (x, y), 6)
            pygame.draw.circle(screen, (150, 255, 255), (x, y), 3)
        elif kind == "k":
            pygame.draw.circle(screen, (120, 50, 0), (x, y), 10)
            pygame.draw.circle(screen, (255, 140, 30), (x, y), 7)
            pygame.draw.circle(screen, (255, 240, 160), (x, y), 3)
        else:
            pygame.draw.circle(screen, (120, 20, 0), (x, y), 6)
            pygame.draw.circle(screen, (255, 120, 60), (x, y), 4)

    def _draw_bullet(self, screen, weapon, x, y, vx, vy, ammo_index):
        color = WEAPONS[weapon]["color"]
        speed = math.hypot(vx, vy) or 1
        dx, dy = vx / speed, vy / speed
        if weapon == "plasma":
            pygame.draw.circle(screen, (90, 40, 140), (x, y), 9)
            pygame.draw.circle(screen, color, (x, y), 7)
            pygame.draw.circle(screen, (255, 230, 255), (x, y), 3)
        elif weapon == "laser":
            tail = (x - dx * 24, y - dy * 24)
            pygame.draw.line(screen, color, (x, y), tail, 4)
            pygame.draw.line(screen, (255, 220, 220), (x, y), tail, 1)
        elif weapon == "rockets":
            tail = (x - dx * 14, y - dy * 14)
            pygame.draw.line(screen, (200, 200, 210), (x, y), tail, 5)
            pygame.draw.circle(screen, color, (x, y), 3)
            flame = (x - dx * (18 + random.randint(0, 6)), y - dy * (18 + random.randint(0, 6)))
            pygame.draw.line(screen, (255, 120, 30), tail, flame, 3)
        else:
            tail = (x - dx * 14, y - dy * 14)
            pygame.draw.line(screen, color, (x, y), tail, 5)
        if ammo_index:
            # Особые снаряды светятся своим цветом на острие
            pygame.draw.circle(screen, AMMO[AMMO_ORDER[ammo_index]]["color"], (x, y), 3)

    def _draw_ship(self, screen, index, player, coop):
        x, y, hp, max_hp, lives, alive, invuln = player[:7]
        ship = player[12]
        if not alive:
            return
        if invuln and (self.frame // 5) % 2:
            return   # мигание во время неуязвимости
        color = PLAYER_COLORS[index]
        image = self.ship_images[ship]
        half_h = image.get_height() // 2
        # Пламя двигателя
        flame_len = 10 + (self.frame * 7 + index * 3) % 8
        pygame.draw.polygon(screen, color, [(x - 6, y + half_h - 6), (x + 6, y + half_h - 6),
                                            (x, y + half_h + flame_len)])
        if coop:
            outline = self.ship_outline(ship, index)
            screen.blit(outline, outline.get_rect(center=(x, y)))
        screen.blit(image, image.get_rect(center=(x, y)))
        effects = player[14]
        if "shield" in effects:
            radius = max(image.get_width(), image.get_height()) // 2 + 8
            pulse = 2 * math.sin(self.frame * 0.2)
            pygame.draw.circle(screen, (120, 220, 255), (x, y), radius + pulse, 2)
        if "virus" in effects or "radiation" in effects or "corrosion" in effects:
            if self.frame % 6 == 0:
                self.particles.append([x + random.randint(-15, 15), y, random.uniform(-0.5, 0.5), -1,
                                       25, 25, (120, 255, 80) if "radiation" in effects else (255, 90, 90), 2])
        if coop:
            bar = pygame.Rect(x - 24, y + half_h + 4, 48, 4)
            pygame.draw.rect(screen, (60, 0, 0), bar)
            pygame.draw.rect(screen, color, (bar.x, bar.y, int(48 * hp / max_hp), 4))

    def _draw_hud(self, screen, snap, local_index, high_score):
        pygame.draw.rect(screen, (10, 10, 25), (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        pygame.draw.line(screen, (60, 60, 110), (0, HUD_HEIGHT), (SCREEN_WIDTH, HUD_HEIGHT))

        for index, player in enumerate(snap["p"]):
            (x, y, hp, max_hp, lives, alive, invuln, score, coins, weapon,
             kills, connected, ship, ammo, effects) = player
            left = 12 + index * 330
            color = PLAYER_COLORS[index]
            name = PLAYER_NAMES[index]
            if len(snap["p"]) > 1 and index == local_index:
                name += " (вы)"
            if not connected:
                name += " — отключился"
            draw_text(screen, name, 16, color, (left, 5), bold=True)
            draw_text(screen, f"{WEAPONS[weapon]['name']} · {AMMO[ammo]['name']}", 14,
                      (170, 170, 190), (left + 120, 7))

            bar = pygame.Rect(left, 26, 150, 14)
            pygame.draw.rect(screen, (60, 0, 0), bar)
            frac = max(hp, 0) / max_hp
            hp_color = (80, 220, 90) if frac > 0.5 else (240, 200, 40) if frac > 0.25 else (240, 60, 50)
            pygame.draw.rect(screen, hp_color, (bar.x, bar.y, int(bar.width * frac), bar.height))
            pygame.draw.rect(screen, (200, 200, 200), bar, 1)
            draw_text(screen, f"{max(hp, 0)}/{max_hp}", 12, (255, 255, 255), bar.center, "center")

            for i in range(min(lives, 7)):
                screen.blit(self.life_icons[ship], (left + 158 + i * 16, 25))
            draw_coin(screen, (left + 280, 33), 7)
            draw_text(screen, coins, 18, (255, 215, 60), (left + 291, 24), bold=True)

        center = SCREEN_WIDTH // 2 + 190
        world = WORLDS[snap["w"]]
        level_in_world = (snap["lvl"] - 1) % LEVELS_PER_WORLD + 1
        draw_text(screen, f"{world['name']} · {level_in_world}/{LEVELS_PER_WORLD}", 17,
                  (200, 200, 255), (center, 5), "midtop", True)
        score = sum(p[7] for p in snap["p"])
        draw_text(screen, f"Счёт: {score:,}".replace(",", " "), 18, (255, 255, 255),
                  (center, 27), "midtop", True)
        diff = DIFFICULTIES[snap["df"]]
        draw_text(screen, diff["name"], 16, diff["color"], (SCREEN_WIDTH - 12, 5), "topright", True)
        if high_score is not None:
            draw_text(screen, f"Рекорд: {max(high_score, score):,}".replace(",", " "), 15,
                      (180, 180, 180), (SCREEN_WIDTH - 12, 28), "topright")
