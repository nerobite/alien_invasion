import pygame
from pygame.sprite import Sprite
import random

from utils import resource_path

class Star(Sprite):
    """Класс для представления одной звезды на фоне."""
    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen

        # Выбираем случайное изображение звезды
        star_images = [
            resource_path("images/star_1.bmp"),
            resource_path("images/star_2.bmp"),
            resource_path("images/star_3.bmp"),
            resource_path("images/star_4.bmp"),
            resource_path("images/star_5.bmp"),
            resource_path("images/star_6.bmp"),
            resource_path("images/star_7.bmp"),
            resource_path("images/star_8.bmp"),
        ]
        self.image = pygame.image.load(random.choice(star_images))
        self.rect = self.image.get_rect()

        # Случайная позиция на экране
        self.rect.x = random.randint(0, ai_game.settings.screen_width - self.rect.width)
        self.rect.y = random.randint(0, ai_game.settings.screen_height - self.rect.height)
