"""Рисует спрайты кораблей, пришельцев и метеоритов и сохраняет их в images/*.png.

Запуск: python tools/make_sprites.py
Картинки рисуются примитивами pygame в 4-кратном разрешении и сглаживаются
при уменьшении. Любую из них можно заменить своей PNG того же имени.
Координаты точек — доли ширины и высоты спрайта (от 0 до 1).
"""
import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

SCALE = 4
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def light(color, t=0.45):
    return mix(color, (255, 255, 255), t)


def dark(color, t=0.45):
    return mix(color, (0, 0, 0), t)


class Sprite:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.surf = pygame.Surface((w * SCALE, h * SCALE), pygame.SRCALPHA)

    def p(self, x, y):
        return (x * self.w * SCALE, y * self.h * SCALE)

    def poly(self, color, pts, mirror=False, outline=True):
        shapes = [pts] + ([[(1 - x, y) for x, y in pts]] if mirror else [])
        for shape in shapes:
            points = [self.p(x, y) for x, y in shape]
            pygame.draw.polygon(self.surf, color, points)
            if outline:
                pygame.draw.polygon(self.surf, dark(color, 0.6), points, SCALE)

    def ellipse(self, color, cx, cy, rx, ry, outline=True, mirror=False):
        for x in ([cx, 1 - cx] if mirror else [cx]):
            rect = pygame.Rect(0, 0, 2 * rx * self.w * SCALE, 2 * ry * self.h * SCALE)
            rect.center = self.p(x, cy)
            pygame.draw.ellipse(self.surf, color, rect)
            if outline:
                pygame.draw.ellipse(self.surf, dark(color, 0.6), rect, SCALE)

    def line(self, color, a, b, width, mirror=False):
        segments = [(a, b)] + ([((1 - a[0], a[1]), (1 - b[0], b[1]))] if mirror else [])
        for start, end in segments:
            pygame.draw.line(self.surf, color, self.p(*start), self.p(*end), int(width * SCALE))

    def glow(self, color, cx, cy, radius, mirror=False):
        """Светящееся пятно; radius — в пикселях готового спрайта."""
        for x in ([cx, 1 - cx] if mirror else [cx]):
            r = radius * SCALE
            g = pygame.Surface((2 * r + 2, 2 * r + 2), pygame.SRCALPHA)
            for i in range(10, 0, -1):
                pygame.draw.circle(g, color + (int(40 + 215 * (1 - i / 10) ** 2),),
                                   (r + 1, r + 1), r * i / 10)
            self.surf.blit(g, g.get_rect(center=self.p(x, cy)))

    def save(self, name):
        image = pygame.transform.smoothscale(self.surf, (self.w, self.h))
        pygame.image.save(image, os.path.join(OUT, name))
        return image


# ---------------------------------------------------------------- корабли игрока
# Нос корабля смотрит вверх (y = 0).

def interceptor():
    s = Sprite(42, 58)
    blue = (40, 110, 230)
    s.poly(blue, [(0.42, 0.40), (0.03, 0.80), (0.06, 0.91), (0.42, 0.78)], mirror=True)
    s.line((170, 175, 190), (0.10, 0.82), (0.10, 0.60), 1.6, mirror=True)
    s.poly(dark(blue, 0.3), [(0.42, 0.70), (0.25, 0.99), (0.45, 0.92)], mirror=True)
    s.poly((225, 230, 240), [(0.5, 0.0), (0.61, 0.25), (0.61, 0.90), (0.5, 0.97),
                             (0.39, 0.90), (0.39, 0.25)])
    s.poly(light(blue, 0.2), [(0.5, 0.10), (0.54, 0.25), (0.54, 0.86), (0.46, 0.86),
                              (0.46, 0.25)], outline=False)
    s.ellipse((90, 220, 255), 0.5, 0.32, 0.075, 0.10)
    s.ellipse((230, 250, 255), 0.48, 0.29, 0.025, 0.035, outline=False)
    s.glow((120, 200, 255), 0.5, 0.97, 5)
    return s.save("ship_interceptor.png")


def assault():
    s = Sprite(58, 58)
    olive = (110, 145, 70)
    s.poly(dark(olive, 0.15), [(0.40, 0.33), (0.02, 0.58), (0.02, 0.82), (0.40, 0.76)], mirror=True)
    s.poly((80, 85, 90), [(0.11, 0.30), (0.21, 0.30), (0.21, 0.86), (0.11, 0.86)], mirror=True)
    s.line((60, 60, 65), (0.16, 0.30), (0.16, 0.10), 2.2, mirror=True)
    s.poly(light(olive, 0.15), [(0.5, 0.02), (0.62, 0.18), (0.64, 0.85), (0.56, 0.97),
                                (0.44, 0.97), (0.36, 0.85), (0.38, 0.18)])
    s.poly(dark(olive, 0.25), [(0.5, 0.42), (0.6, 0.50), (0.6, 0.80), (0.4, 0.80), (0.4, 0.50)])
    s.line((230, 200, 70), (0.42, 0.58), (0.58, 0.58), 1.2)
    s.ellipse((255, 200, 80), 0.5, 0.25, 0.07, 0.09)
    s.ellipse((255, 245, 200), 0.485, 0.22, 0.02, 0.03, outline=False)
    s.glow((255, 170, 60), 0.44, 0.96, 4, mirror=True)
    return s.save("ship_assault.png")


def fortress():
    s = Sprite(62, 64)
    steel, orange = (150, 155, 170), (235, 130, 40)
    s.poly(dark(steel, 0.25), [(0.30, 0.14), (0.04, 0.34), (0.04, 0.86), (0.30, 0.95)], mirror=True)
    s.poly(orange, [(0.07, 0.50), (0.13, 0.50), (0.13, 0.76), (0.07, 0.76)], mirror=True)
    s.poly(steel, [(0.5, 0.0), (0.72, 0.12), (0.74, 0.90), (0.5, 1.0), (0.26, 0.90), (0.28, 0.12)])
    s.poly(orange, [(0.5, 0.18), (0.62, 0.28), (0.62, 0.60), (0.5, 0.70), (0.38, 0.60), (0.38, 0.28)])
    s.line(dark(steel, 0.4), (0.30, 0.78), (0.70, 0.78), 1)
    s.line((70, 70, 80), (0.17, 0.40), (0.17, 0.16), 2.2, mirror=True)
    s.ellipse((120, 125, 140), 0.17, 0.42, 0.08, 0.075, mirror=True)
    s.ellipse((90, 230, 255), 0.5, 0.40, 0.065, 0.075)
    s.glow((255, 150, 60), 0.36, 0.97, 4, mirror=True)
    return s.save("ship_fortress.png")


def phantom():
    s = Sprite(52, 62)
    body, edge = (60, 30, 95), (255, 70, 225)
    s.poly(body, [(0.5, 0.0), (0.0, 0.82), (0.16, 0.92), (0.5, 0.72)], mirror=True)
    s.line(edge, (0.5, 0.02), (0.02, 0.82), 1.1, mirror=True)
    s.poly((95, 55, 140), [(0.5, 0.10), (0.63, 0.60), (0.5, 0.96), (0.37, 0.60)])
    s.line(edge, (0.5, 0.55), (0.5, 0.88), 0.8)
    s.ellipse(light(edge, 0.3), 0.5, 0.40, 0.055, 0.11)
    s.glow((255, 90, 230), 0.42, 0.90, 4, mirror=True)
    return s.save("ship_phantom.png")


# ---------------------------------------------------------------- пришельцы
# Нос смотрит вниз (y = 1).

def scout():
    s = Sprite(40, 30)
    green = (90, 220, 90)
    s.poly(dark(green, 0.3), [(0.30, 0.60), (0.18, 1.0), (0.28, 0.96), (0.42, 0.70)], mirror=True)
    s.poly((70, 170, 120), [(0.36, 0.28), (0.0, 0.12), (0.05, 0.55), (0.36, 0.62)], mirror=True)
    s.ellipse(light(green, 0.15), 0.5, 0.45, 0.22, 0.36)
    s.ellipse((255, 240, 80), 0.5, 0.56, 0.10, 0.14)
    s.ellipse((40, 20, 0), 0.5, 0.60, 0.04, 0.06, outline=False)
    return s.save("alien_scout.png")


def soldier():
    s = Sprite(44, 34)
    yellow = (240, 200, 50)
    s.poly(dark(yellow, 0.2), [(0.40, 0.08), (0.0, 0.18), (0.10, 0.60), (0.40, 0.75)], mirror=True)
    s.line((70, 70, 75), (0.20, 0.45), (0.20, 0.98), 2.6, mirror=True)
    s.poly(yellow, [(0.30, 0.0), (0.70, 0.0), (0.62, 0.70), (0.5, 1.0), (0.38, 0.70)])
    s.ellipse((230, 50, 40), 0.5, 0.38, 0.08, 0.13)
    s.glow((255, 200, 120), 0.5, 0.36, 2)
    return s.save("alien_soldier.png")


def kamikaze():
    s = Sprite(36, 34)
    red = (230, 60, 40)
    s.glow((255, 160, 40), 0.5, 0.05, 6)
    s.poly(dark(red, 0.3), [(0.40, 0.28), (0.0, 0.0), (0.30, 0.55)], mirror=True)
    s.poly(dark(red, 0.15), [(0.40, 0.58), (0.04, 0.76), (0.42, 0.82)], mirror=True)
    s.poly(red, [(0.32, 0.05), (0.68, 0.05), (0.60, 0.60), (0.5, 1.0), (0.40, 0.60)])
    s.glow((255, 210, 80), 0.5, 0.36, 4)
    return s.save("alien_kamikaze.png")


def tank():
    s = Sprite(60, 40)
    purple = (140, 80, 200)
    s.poly((60, 50, 70), [(0.0, 0.04), (0.18, 0.04), (0.18, 0.96), (0.0, 0.96)], mirror=True)
    for i in range(6):
        y = 0.12 + i * 0.15
        s.line((110, 100, 120), (0.02, y), (0.16, y), 1, mirror=True)
    s.poly(purple, [(0.15, 0.10), (0.85, 0.10), (0.90, 0.60), (0.70, 0.92), (0.30, 0.92), (0.10, 0.60)])
    s.poly(dark(purple, 0.25), [(0.25, 0.2), (0.75, 0.2), (0.75, 0.32), (0.25, 0.32)], outline=False)
    s.line((70, 60, 80), (0.5, 0.5), (0.5, 1.0), 3.2)
    s.ellipse(light(purple, 0.25), 0.5, 0.48, 0.15, 0.24)
    s.glow((255, 120, 255), 0.5, 0.48, 3)
    return s.save("alien_tank.png")


def bomber():
    s = Sprite(64, 34)
    brown = (200, 120, 50)
    s.poly(brown, [(0.5, 0.04), (1.0, 0.55), (0.90, 0.78), (0.5, 0.56), (0.10, 0.78), (0.0, 0.55)])
    s.poly(dark(brown, 0.2), [(0.5, 0.20), (0.80, 0.52), (0.5, 0.44), (0.20, 0.52)], outline=False)
    s.ellipse(dark(brown, 0.35), 0.5, 0.48, 0.12, 0.42)
    s.ellipse((60, 60, 65), 0.36, 0.70, 0.05, 0.13, mirror=True)
    s.glow((255, 60, 40), 0.06, 0.58, 3, mirror=True)
    s.ellipse((255, 220, 120), 0.5, 0.42, 0.05, 0.13)
    return s.save("alien_bomber.png")


def sniper():
    s = Sprite(34, 44)
    cyan = (60, 200, 220)
    s.poly(dark(cyan, 0.3), [(0.38, 0.0), (0.0, 0.08), (0.10, 0.42), (0.40, 0.46)], mirror=True)
    s.line((90, 90, 100), (0.5, 0.50), (0.5, 1.0), 2.2)
    s.line((200, 230, 240), (0.42, 0.96), (0.58, 0.96), 1.2)
    s.poly(cyan, [(0.36, 0.0), (0.64, 0.0), (0.62, 0.58), (0.5, 0.70), (0.38, 0.58)])
    s.glow((255, 60, 60), 0.5, 0.30, 4)
    return s.save("alien_sniper.png")


def splitter():
    s = Sprite(46, 32)
    pink = (240, 100, 180)
    s.poly(dark(pink, 0.3), [(0.3, 0.35), (0.7, 0.35), (0.7, 0.65), (0.3, 0.65)])
    s.ellipse(pink, 0.28, 0.5, 0.27, 0.45, mirror=True)
    s.ellipse((255, 255, 255), 0.28, 0.58, 0.09, 0.14, mirror=True)
    s.ellipse((60, 0, 40), 0.28, 0.62, 0.04, 0.07, outline=False, mirror=True)
    return s.save("alien_splitter.png")


def mini():
    s = Sprite(24, 20)
    pink = (255, 140, 200)
    s.ellipse(pink, 0.5, 0.5, 0.46, 0.44)
    s.ellipse((255, 255, 255), 0.5, 0.6, 0.18, 0.2)
    s.ellipse((60, 0, 40), 0.5, 0.65, 0.08, 0.1, outline=False)
    return s.save("alien_mini.png")


# ---------------------------------------------------------------- боссы

def mothership():
    s = Sprite(200, 110)
    crimson = (200, 40, 70)
    s.ellipse(dark(crimson, 0.3), 0.5, 0.76, 0.22, 0.14)
    s.ellipse(crimson, 0.5, 0.56, 0.5, 0.27)
    s.ellipse(light(crimson, 0.15), 0.5, 0.50, 0.42, 0.14, outline=False)
    s.ellipse((255, 160, 200), 0.5, 0.34, 0.22, 0.30)
    s.ellipse((255, 230, 240), 0.44, 0.24, 0.06, 0.08, outline=False)
    for i in range(9):
        x = 0.1 + i * 0.1
        y = 0.56 + 0.2 * math.sin(math.pi * (x - 0.0)) * 0.5
        s.glow((255, 230, 120), x, y, 4)
    s.glow((120, 255, 120), 0.5, 0.82, 7)
    return s.save("boss_mothership.png")


def cruiser():
    s = Sprite(240, 90)
    gray = (130, 140, 155)
    s.poly(gray, [(0.04, 0.30), (0.96, 0.30), (1.0, 0.50), (0.90, 0.70), (0.60, 0.76),
                  (0.5, 1.0), (0.40, 0.76), (0.10, 0.70), (0.0, 0.50)])
    s.poly(dark(gray, 0.2), [(0.10, 0.45), (0.90, 0.45), (0.86, 0.58), (0.14, 0.58)], outline=False)
    s.poly(dark(gray, 0.35), [(0.42, 0.0), (0.58, 0.0), (0.62, 0.36), (0.38, 0.36)])
    s.ellipse((110, 200, 255), 0.5, 0.15, 0.04, 0.08)
    for x in (0.18, 0.32, 0.68, 0.82):
        s.line((60, 60, 70), (x, 0.55), (x, 0.88), 3)
        s.ellipse((100, 105, 120), x, 0.55, 0.035, 0.12)
    for i in range(12):
        s.glow((255, 60, 60), 0.12 + i * 0.07, 0.36, 2)
    return s.save("boss_cruiser.png")


def guardian():
    s = Sprite(160, 160)
    teal = (60, 220, 200)
    center = s.p(0.5, 0.5)
    pygame.draw.circle(s.surf, dark(teal, 0.4), center, 70 * SCALE, 9 * SCALE)
    pygame.draw.circle(s.surf, teal, center, 70 * SCALE, 4 * SCALE)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tip = (0.5 + 0.48 * math.cos(a), 0.5 + 0.48 * math.sin(a))
        left = (0.5 + 0.18 * math.cos(a - 0.5), 0.5 + 0.18 * math.sin(a - 0.5))
        right = (0.5 + 0.18 * math.cos(a + 0.5), 0.5 + 0.18 * math.sin(a + 0.5))
        s.poly(light(teal, 0.2), [left, tip, right])
    s.poly(teal, [(0.5, 0.18), (0.72, 0.5), (0.5, 0.82), (0.28, 0.5)])
    s.poly(light(teal, 0.5), [(0.5, 0.30), (0.6, 0.5), (0.5, 0.70), (0.4, 0.5)], outline=False)
    s.glow((255, 255, 255), 0.5, 0.5, 12)
    return s.save("boss_guardian.png")


def emperor():
    s = Sprite(230, 140)
    gold, black = (230, 190, 60), (45, 30, 50)
    s.poly(dark(gold, 0.2), [(0.40, 0.25), (0.0, 0.10), (0.08, 0.60), (0.30, 0.80)], mirror=True)
    s.poly(gold, [(0.30, 0.05), (0.18, 0.0), (0.25, 0.30)], mirror=True)
    s.poly(gold, [(0.42, 0.0), (0.38, 0.0), (0.40, 0.2)], mirror=True)
    s.poly(black, [(0.30, 0.10), (0.70, 0.10), (0.78, 0.55), (0.60, 0.90), (0.5, 1.0),
                   (0.40, 0.90), (0.22, 0.55)])
    s.poly(gold, [(0.5, 0.18), (0.64, 0.40), (0.5, 0.75), (0.36, 0.40)])
    s.ellipse((200, 20, 30), 0.5, 0.45, 0.06, 0.12)
    s.glow((255, 60, 40), 0.5, 0.45, 10)
    s.line((90, 80, 90), (0.30, 0.6), (0.30, 0.95), 4, mirror=True)
    s.glow((255, 210, 80), 0.12, 0.40, 5, mirror=True)
    return s.save("boss_emperor.png")


# ---------------------------------------------------------------- метеориты

def meteor(size, name, seed):
    rng = random.Random(seed)
    s = Sprite(size, size)
    rock = (125, 108, 95)
    points = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        r = 0.5 * rng.uniform(0.74, 0.98)
        points.append((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)))
    s.poly(rock, points)
    s.poly(light(rock, 0.18), [(0.5 + (x - 0.5) * 0.7 - 0.06, 0.5 + (y - 0.5) * 0.7 - 0.06)
                               for x, y in points], outline=False)
    for _ in range(5):
        cx, cy = rng.uniform(0.3, 0.7), rng.uniform(0.3, 0.7)
        r = rng.uniform(0.05, 0.11)
        s.ellipse(dark(rock, 0.25), cx, cy, r, r, outline=False)
        s.ellipse(dark(rock, 0.45), cx + r * 0.2, cy + r * 0.2, r * 0.7, r * 0.7, outline=False)
    return s.save(name)


# ---------------------------------------------------------------- космический мусор

def wreck_hull():
    """Обломок корабля: разорванный корпус с торчащими балками."""
    s = Sprite(70, 50)
    hull = (120, 125, 135)
    s.poly(dark(hull, 0.25), [(0.05, 0.35), (0.35, 0.10), (0.75, 0.15), (0.70, 0.40),
                              (0.85, 0.55), (0.60, 0.90), (0.40, 0.70), (0.15, 0.85)])
    s.poly(hull, [(0.12, 0.38), (0.36, 0.20), (0.66, 0.24), (0.62, 0.45), (0.74, 0.56),
                  (0.56, 0.80), (0.40, 0.62), (0.20, 0.72)])
    # Рваный край и балки
    for a, b in (((0.70, 0.40), (0.98, 0.30)), ((0.62, 0.80), (0.80, 0.98)), ((0.10, 0.80), (0.0, 0.98))):
        s.line((90, 90, 95), a, b, 2.2)
    s.poly((60, 60, 70), [(0.30, 0.35), (0.50, 0.33), (0.48, 0.50), (0.30, 0.52)])
    s.ellipse((90, 200, 255), 0.40, 0.42, 0.06, 0.07)
    s.poly((200, 80, 40), [(0.18, 0.55), (0.30, 0.50), (0.28, 0.62)], outline=False)
    s.glow((255, 180, 60), 0.86, 0.52, 4)
    s.glow((255, 120, 40), 0.60, 0.86, 3)
    return s.save("wreck_hull.png")


def wreck_wing():
    """Обломок крыла с двигателем."""
    s = Sprite(60, 46)
    metal = (150, 120, 90)
    s.poly(metal, [(0.02, 0.60), (0.45, 0.08), (0.70, 0.12), (0.60, 0.45), (0.95, 0.70),
                   (0.70, 0.95), (0.30, 0.80)])
    s.poly(dark(metal, 0.3), [(0.20, 0.60), (0.48, 0.25), (0.58, 0.28), (0.40, 0.70)], outline=False)
    s.ellipse((80, 80, 90), 0.75, 0.75, 0.13, 0.17)
    s.ellipse((40, 40, 45), 0.75, 0.75, 0.07, 0.09, outline=False)
    s.line((90, 90, 95), (0.70, 0.12), (0.92, 0.0), 2)
    s.glow((255, 200, 80), 0.94, 0.68, 4)
    return s.save("wreck_wing.png")


def crate():
    """Контейнер из обломков; содержимое неизвестно, пока не подберешь."""
    s = Sprite(30, 30)
    gold = (220, 170, 50)
    s.glow((255, 230, 120), 0.5, 0.5, 15)
    s.poly(gold, [(0.15, 0.15), (0.85, 0.15), (0.85, 0.85), (0.15, 0.85)])
    s.poly(dark(gold, 0.3), [(0.15, 0.42), (0.85, 0.42), (0.85, 0.58), (0.15, 0.58)], outline=False)
    s.line(dark(gold, 0.5), (0.5, 0.15), (0.5, 0.85), 1.5)
    image = s.save("crate.png")
    return image


SPRITES = [interceptor, assault, fortress, phantom,
           scout, soldier, kamikaze, tank, bomber, sniper, splitter, mini,
           mothership, cruiser, guardian, emperor,
           lambda: meteor(72, "meteor_big.png", 7), lambda: meteor(38, "meteor_small.png", 3),
           wreck_hull, wreck_wing, crate]


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    images = [make() for make in SPRITES]
    print(f"Сохранено {len(images)} спрайтов в {OUT}")
    return images


if __name__ == "__main__":
    main()
