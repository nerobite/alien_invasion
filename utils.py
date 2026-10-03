import os
import sys

import pygame


def resource_path(relative_path: str) -> str:
    """
    Возвращает путь к ресурсу как при разработке, так и из exe.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller запустил exe
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def data_path(filename: str) -> str:
    """Путь к файлу сохранения: рядом с exe или со скриптами игры."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


_font_cache = {}


def get_font(size, bold=False):
    """Шрифт с поддержкой кириллицы (кэшируется)."""
    key = (size, bold)
    if key not in _font_cache:
        path = None
        for name in ("arial", "segoeui", "dejavusans", "liberationsans"):
            path = pygame.font.match_font(name, bold=bold)
            if path and "ARIALN" not in path.upper():
                break
            path = None
        _font_cache[key] = pygame.font.Font(path, size)
    return _font_cache[key]


def draw_text(surface, text, size, color, pos, anchor="topleft", bold=False):
    """Выводит текст и возвращает его прямоугольник."""
    image = get_font(size, bold).render(str(text), True, color)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)
    return rect


def draw_coin(surface, center, radius=8):
    """Рисует значок монеты."""
    pygame.draw.circle(surface, (255, 200, 40), center, radius)
    pygame.draw.circle(surface, (255, 240, 150), center, max(2, radius - 3), 2)


def silhouette(image, color=(255, 255, 255)):
    """Одноцветный силуэт картинки (вспышка при попадании)."""
    mask = pygame.mask.from_surface(image)
    return mask.to_surface(setcolor=color + (255,), unsetcolor=(0, 0, 0, 0))
