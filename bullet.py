import math

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WEAPONS, AMMO


def _off_screen(x, y, margin=30):
    return (y < -margin or y > SCREEN_HEIGHT + margin
            or x < -margin or x > SCREEN_WIDTH + margin)


class Bullet:
    """Снаряд, выпущенный кораблем игрока. Свойства зависят от оружия и типа снарядов."""

    def __init__(self, owner, weapon_id, ammo_id, x, y, angle_deg, damage_mult):
        weapon, ammo = WEAPONS[weapon_id], AMMO[ammo_id]
        self.owner = owner
        self.weapon = weapon_id
        self.ammo = ammo_id
        self.speed = weapon["speed"]
        angle = math.radians(angle_deg)
        self.vx = self.speed * math.sin(angle)
        self.vy = -self.speed * math.cos(angle)
        self.x, self.y = float(x), float(y)
        self.rect = pygame.Rect(0, 0, *weapon["size"])
        self.rect.center = (round(x), round(y))
        self.damage = weapon["damage"] * ammo["damage"] * damage_mult
        self.pierce = weapon["pierce"] + ammo["pierce"]
        self.splash = max(weapon["splash"], ammo["splash"])
        self.slow = ammo["slow"]
        self.homing = weapon["homing"]
        self.hit_ids = set()   # цели, уже пробитые этим снарядом
        self.target = None
        self.age = 0

    def update(self, aliens):
        self.age += 1
        if self.homing and self.age > 8:
            self._steer(aliens)
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (round(self.x), round(self.y))

    def _steer(self, aliens):
        """Самонаведение: плавно поворачивает к ближайшему пришельцу."""
        if self.target is None or self.target.dead:
            self.target = min(aliens, default=None,
                              key=lambda a: (a.x - self.x) ** 2 + (a.y - self.y) ** 2)
        self.speed = min(self.speed * 1.03, 12)
        current = math.atan2(self.vy, self.vx)
        if self.target is not None:
            desired = math.atan2(self.target.y - self.y, self.target.x - self.x)
            diff = (desired - current + math.pi) % (2 * math.pi) - math.pi
            current += max(-0.09, min(0.09, diff))
        self.vx = self.speed * math.cos(current)
        self.vy = self.speed * math.sin(current)

    def off_screen(self):
        return _off_screen(self.x, self.y)


class EnemyBullet:
    """Снаряд пришельцев. kind: 'o' — обычный, 'b' — крупный,
    's' — быстрая пуля снайпера, 'k' — бомба, 'g' — зеленый лазерный заряд."""

    SIZES = {"o": 9, "b": 14, "s": 8, "k": 16, "g": 7}

    def __init__(self, x, y, vx, vy, damage, kind="o"):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.kind = kind
        size = self.SIZES[kind]
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (round(x), round(y))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (round(self.x), round(self.y))

    def off_screen(self):
        return _off_screen(self.x, self.y)
