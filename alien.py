import itertools
import math
import random

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ALIEN_TYPES

# Общий счетчик id для пришельцев и метеоритов (снаряд помнит, кого уже пробил)
entity_ids = itertools.count(1)


class Alien:
    """Один пришелец (только логика, без отрисовки).

    state: 'formation' — летит в строю флота,
           'dive'      — пикирует на игрока (камикадзе, осколки),
           'boss'      — босс, двигается и атакует по своему расписанию.
    """

    def __init__(self, kind, x, y, level, hp_scale, coin_mult=1.0, fire_mult=1.0):
        info = ALIEN_TYPES[kind]
        self.id = next(entity_ids)
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.rect = pygame.Rect(0, 0, *info["size"])
        self.rect.center = (round(x), round(y))

        self.is_boss = info.get("boss", False)
        self.state = "boss" if self.is_boss else "formation"
        base_coins = info["coins"] + (10 * level if self.is_boss else (level - 1) // 5)
        self.coins = max(1, round(base_coins * coin_mult))
        self.max_hp = self.hp = info["hp"] * hp_scale
        self.points = int(info["points"] * (1 + 0.1 * (level - 1)))
        self.shoot_chance = info["shoot"] * (1 + 0.08 * (level - 1)) * fire_mult
        self.ram_damage = info["ram"]
        self.dives = info.get("dive", False)

        self.dead = False
        self.flash = 0                    # кадры белой вспышки после попадания
        self.slowed = 0                   # кадры замедления ледяными снарядами
        self.vx = 0.0
        self.dive_speed = min(3.0 + 0.15 * level, 6.0)
        self.dive_timer = random.randint(150, 700)
        self.timer = 0
        # Высота, на которой висит босс
        self.hover_y = 60 + self.rect.height / 2 + 20

    @property
    def speed_factor(self):
        return 0.5 if self.slowed else 1.0

    def update(self, world):
        if self.flash:
            self.flash -= 1
        if self.slowed:
            self.slowed -= 1
        self.timer += 1
        k = self.speed_factor

        if self.state == "formation":
            if self.dives:
                self.dive_timer -= 1
                if self.dive_timer <= 0:
                    self.state = "dive"
            if self.shoot_chance and random.random() < self.shoot_chance * k:
                world.alien_fire(self)

        elif self.state == "dive":
            target = world.nearest_player(self.x, self.y)
            if target is not None:
                pull = (target.x - self.x) * 0.02
                self.vx += max(-0.25, min(0.25, pull))
                self.vx = max(-3.0, min(3.0, self.vx))
            self.x += self.vx * k
            self.y += self.dive_speed * k
            if self.y > SCREEN_HEIGHT + 40:
                # Пролетел мимо — заходит на новый круг сверху
                self.y = -40
                self.x = random.uniform(40, SCREEN_WIDTH - 40)
                self.vx = 0.0

        elif self.state == "boss":
            self._boss_move(k)
            world.boss_attack(self)

        self.rect.center = (round(self.x), round(self.y))

    def _boss_move(self, k):
        t = self.timer * 0.008 * k
        swing = SCREEN_WIDTH / 2 - self.rect.width / 2 - 20
        target_y = self.hover_y
        if self.kind == "guardian":
            # Страж летает «восьмеркой»
            target_y += 50 * math.sin(2 * t)
        self.y += (target_y - self.y) * 0.03
        self.x = SCREEN_WIDTH / 2 + swing * math.sin(t)
