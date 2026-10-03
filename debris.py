import random

import pygame

from alien import entity_ids
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WRECKS


class Wreck:
    """Обломок разбитого корабля, медленно дрейфующий по полю.
    Если расстрелять — выпадает контейнер с сюрпризом (Pickup)."""

    def __init__(self, variant, hp_scale=1.0):
        info = WRECKS[variant]
        self.id = next(entity_ids)
        self.variant = variant
        self.x = random.uniform(60, SCREEN_WIDTH - 60)
        self.y = -40.0
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(0.7, 1.3)
        self.rect = pygame.Rect(0, 0, *info["size"])
        self.rect.center = (round(self.x), round(self.y))
        self.max_hp = self.hp = info["hp"] * hp_scale
        self.damage = info["damage"]
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-0.8, 0.8)
        self.flash = 0
        self.dead = False

    def update(self):
        if self.flash:
            self.flash -= 1
        self.x += self.vx
        self.y += self.vy
        self.angle = (self.angle + self.spin) % 360
        self.rect.center = (round(self.x), round(self.y))

    def off_screen(self):
        return self.y > SCREEN_HEIGHT + 60 or self.x < -80 or self.x > SCREEN_WIDTH + 80


class Pickup:
    """Контейнер «?», выпавший из обломка. Падает вниз, подбирается кораблем."""

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (round(x), round(y))
        self.dead = False

    def update(self):
        self.y += 1.4
        self.rect.center = (round(self.x), round(self.y))

    def off_screen(self):
        return self.y > SCREEN_HEIGHT + 30
