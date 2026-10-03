import sys

import pygame

from player_profile import Profile
from renderer import Renderer
from scenes import MenuScene
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_COLOR
from star import Starfield
from utils import resource_path


class AlienInvasion:
    """Класс для управления ресурсами и поведением игры.

    Игра состоит из экранов-сцен (меню, магазин, игра, сеть — см. scenes.py).
    Основной цикл передает события, обновление и отрисовку текущей сцене.
    """

    def __init__(self, windowed=False):
        """Инициализирует игру и создает игровые ресурсы"""
        pygame.init()
        flags = pygame.SCALED if windowed else pygame.SCALED | pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Alien Invasion")
        pygame.display.set_icon(pygame.image.load(resource_path("images/ship_2.png")))
        self.clock = pygame.time.Clock()

        self.profile = Profile()
        self.starfield = Starfield()
        self.renderer = Renderer()
        self.scene = MenuScene(self)

    def switch(self, scene, close=True):
        """Переключает экран. close=False — старый экран еще понадобится."""
        if close:
            self.scene.on_exit()
        self.scene = scene

    def run_game(self):
        """Запуск основного цикла игры"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                else:
                    self.scene.handle_event(event)
            self.scene.update()
            self.screen.fill(BG_COLOR)
            self.scene.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

    def quit(self):
        self.scene.on_exit()
        self.profile.save()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    # --window — запуск в окне (удобно, чтобы проверить сеть на одном ПК)
    ai = AlienInvasion(windowed="--window" in sys.argv)
    ai.run_game()
