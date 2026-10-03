import random

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from utils import resource_path


class Starfield:
    """Звездное небо, медленно плывущее вниз (параллакс в три слоя)."""

    def __init__(self, count=110):
        images = []
        for i in range(1, 9):
            image = pygame.image.load(resource_path(f"images/star_{i}.bmp")).convert()
            image.set_colorkey((0, 0, 0))
            images.append(image)

        self.stars = []
        for _ in range(count):
            layer = random.choice((1, 2, 3))
            base = random.choice(images)
            # Мелкие и тусклые, чтобы не путались со снарядами
            size = random.randint(2, 3) * layer + 1
            image = pygame.transform.smoothscale(base, (size, size))
            image.set_colorkey((0, 0, 0))
            image.set_alpha(90 + 50 * layer)
            self.stars.append([image, random.uniform(0, SCREEN_WIDTH),
                               random.uniform(0, SCREEN_HEIGHT), 0.12 * layer])

    def update(self, speed=1.0):
        for star in self.stars:
            star[2] += star[3] * speed
            if star[2] > SCREEN_HEIGHT:
                star[2] = -star[0].get_height()
                star[1] = random.uniform(0, SCREEN_WIDTH)

    def draw(self, screen):
        for image, x, y, _ in self.stars:
            screen.blit(image, (x, y))
