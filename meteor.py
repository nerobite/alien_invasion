import random

import pygame

from alien import entity_ids
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, METEORS


class Meteor:
    """Блуждающий метеорит: разбивает и пришельцев, и корабли игроков.
    big=1 — большой (при уничтожении раскалывается на два малых), 0 — малый."""

    def __init__(self, big, x, y, vx, vy, hp_scale=1.0):
        info = METEORS[big]
        self.id = next(entity_ids)
        self.big = big
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.radius = info["radius"]
        self.rect = pygame.Rect(0, 0, 2 * self.radius, 2 * self.radius)
        self.rect.center = (round(x), round(y))
        self.max_hp = self.hp = info["hp"] * hp_scale
        self.damage = info["damage"]
        self.points = info["points"]
        self.coins = info["coins"]
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-2.5, 2.5)
        self.hit_ids = set()   # пришельцы, которых метеорит уже задел
        self.flash = 0
        self.dead = False

    @classmethod
    def random_spawn(cls, hp_scale, speed_mult=1.0):
        """Большой или малый метеорит, влетающий сверху или сбоку."""
        big = 1 if random.random() < 0.6 else 0
        vy = random.uniform(1.2, 2.6) * speed_mult
        if random.random() < 0.7:
            x, y = random.uniform(40, SCREEN_WIDTH - 40), -40
            vx = random.uniform(-1.6, 1.6)
        else:
            from_left = random.random() < 0.5
            x = -40 if from_left else SCREEN_WIDTH + 40
            y = random.uniform(60, SCREEN_HEIGHT * 0.4)
            vx = random.uniform(1.5, 3.0) * (1 if from_left else -1)
        return cls(big, x, y, vx, vy, hp_scale)

    def update(self):
        if self.flash:
            self.flash -= 1
        self.x += self.vx
        self.y += self.vy
        self.angle = (self.angle + self.spin) % 360
        self.rect.center = (round(self.x), round(self.y))

    def collides(self, rect):
        """Касание круга метеорита с прямоугольником."""
        nearest_x = min(max(self.x, rect.left), rect.right)
        nearest_y = min(max(self.y, rect.top), rect.bottom)
        return (nearest_x - self.x) ** 2 + (nearest_y - self.y) ** 2 <= self.radius ** 2

    def fragments(self):
        """Два малых осколка, разлетающихся в стороны."""
        return [Meteor(0, self.x + dx * 12, self.y, self.vx + dx * 1.4, self.vy * 0.9,
                       self.max_hp / METEORS[1]["hp"])
                for dx in (-1, 1)]

    def off_screen(self):
        return (self.y > SCREEN_HEIGHT + 60 or self.x < -80
                or self.x > SCREEN_WIDTH + 80 or self.y < -120)
