"""Общие элементы интерфейса экранов."""
import pygame

from button import Button
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WORLDS, DIFFICULTIES, DIFFICULTY_ORDER,
                      ALIEN_TYPES, LEVELS_PER_WORLD)
from utils import draw_text, draw_coin, get_font

CENTER_X = SCREEN_WIDTH // 2


def dim_screen(screen, alpha=170):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 10, alpha))
    screen.blit(overlay, (0, 0))


def draw_panel(screen, rect, border=(90, 90, 160)):
    pygame.draw.rect(screen, (18, 18, 40), rect, border_radius=12)
    pygame.draw.rect(screen, border, rect, 2, border_radius=12)


def draw_coins(screen, amount, pos, size=28, anchor="topright"):
    """Сумма монет со значком; pos — точка привязки текста."""
    rect = draw_text(screen, f"{amount:,}".replace(",", " "), size, (255, 215, 60),
                     pos, anchor, bold=True)
    draw_coin(screen, (rect.left - size // 2 - 2, rect.centery), size // 3)
    return rect


def draw_wrapped(screen, text, size, color, pos, width, line_gap=2):
    """Текст с переносом по словам; возвращает y под последней строкой."""
    font = get_font(size)
    x, y = pos
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] > width and line:
            draw_text(screen, line, size, color, (x, y))
            y += font.get_linesize() + line_gap
            line = word
        else:
            line = candidate
    if line:
        draw_text(screen, line, size, color, (x, y))
        y += font.get_linesize() + line_gap
    return y


class MissionPanel:
    """Выбор сложности и стартового мира (перед одиночной игрой и в лобби хоста).
    Выбор запоминается в профиле."""

    def __init__(self, profile, x, y, width=640):
        self.profile = profile
        self.x, self.y, self.width = x, y, width
        bw = (width - 30) // 4
        self.diff_buttons = [Button((x + i * (bw + 10), y + 34, bw, 44), DIFFICULTIES[d]["name"], 20,
                                    tuple(c // 2 for c in DIFFICULTIES[d]["color"]))
                             for i, d in enumerate(DIFFICULTY_ORDER)]
        # Миры — два ряда по 5 кнопок
        ww = (width - 40) // 5
        self.world_buttons = [Button((x + (i % 5) * (ww + 10), y + 172 + (i // 5) * 46, ww, 40),
                                     str(i + 1), 20, (40, 70, 120))
                              for i in range(len(WORLDS))]

    @property
    def difficulty(self):
        return self.profile.difficulty

    @property
    def world(self):
        return min(self.profile.start_world, self.profile.unlocked_world)

    def handle_event(self, event):
        """Возвращает True, если выбор изменился."""
        for button, diff in zip(self.diff_buttons, DIFFICULTY_ORDER):
            if button.clicked(event):
                self.profile.difficulty = diff
                return True
        for i, button in enumerate(self.world_buttons):
            if button.clicked(event):
                self.profile.start_world = i
                return True
        return False

    def draw(self, screen):
        x, y = self.x, self.y
        draw_text(screen, "Сложность", 22, (200, 200, 255), (x, y), bold=True)
        for button, diff in zip(self.diff_buttons, DIFFICULTY_ORDER):
            button.draw(screen)
            if diff == self.difficulty:
                pygame.draw.rect(screen, (255, 215, 60), button.rect, 3, border_radius=8)
        d = DIFFICULTIES[self.difficulty]
        draw_text(screen, f"Враги: здоровье x{d['hp']:g}, урон x{d['damage']:g}, "
                          f"скорость x{d['speed']:g}", 17, (200, 200, 200), (x, y + 86))
        draw_text(screen, f"Монеты x{d['coins']:g}", 20, (255, 215, 60), (x, y + 108), bold=True)

        draw_text(screen, "Стартовый мир", 22, (200, 200, 255), (x, y + 142), bold=True)
        for i, button in enumerate(self.world_buttons):
            button.enabled = i <= self.profile.unlocked_world
            button.text = f"Мир {i + 1}" if button.enabled else "Закрыт"
            button.draw(screen)
            if i == self.world:
                pygame.draw.rect(screen, (255, 215, 60), button.rect, 3, border_radius=8)
        world = WORLDS[self.world]
        enemies = ", ".join(ALIEN_TYPES[k]["name"].lower() for k in world["enemies"])
        draw_text(screen, f"Мир {self.world + 1}: {world['name']}", 22, (255, 255, 255),
                  (x, y + 270), bold=True)
        bottom = draw_wrapped(screen, f"Враги: {enemies}. Босс: {ALIEN_TYPES[world['boss']]['name'].capitalize()}"
                                      f" (уровень {LEVELS_PER_WORLD}).", 17, (200, 200, 200),
                              (x, y + 298), self.width)
        meteors = "очень много" if world["meteors"] >= 2 else "много" if world["meteors"] >= 1 else "мало"
        draw_text(screen, f"Метеоритов: {meteors}. Следующий мир открывается после победы над боссом.",
                  17, (200, 200, 200), (x, bottom))
