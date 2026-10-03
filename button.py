import pygame

from utils import draw_text


class Button:
    """Кнопка интерфейса с подсветкой при наведении."""

    def __init__(self, rect, text, size=30, color=(40, 160, 70), enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.size = size
        self.color = color
        self.enabled = enabled

    def draw(self, screen):
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if not self.enabled:
            color = (60, 60, 70)
        elif hover:
            color = tuple(min(255, c + 40) for c in self.color)
        else:
            color = self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (230, 230, 230) if hover else (20, 20, 20),
                         self.rect, 2, border_radius=8)
        text_color = (255, 255, 255) if self.enabled else (150, 150, 150)
        draw_text(screen, self.text, self.size, text_color, self.rect.center, "center", True)

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))


class TextInput:
    """Поле ввода текста (используется для IP-адреса)."""

    def __init__(self, rect, text="", allowed="0123456789.", max_len=15):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.allowed = allowed
        self.max_len = max_len
        self.active = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                self._paste()
            elif event.unicode and event.unicode in self.allowed and len(self.text) < self.max_len:
                self.text += event.unicode

    def _paste(self):
        try:
            text = pygame.scrap.get_text() if hasattr(pygame.scrap, "get_text") else ""
        except pygame.error:
            text = ""
        for ch in text or "":
            if ch in self.allowed and len(self.text) < self.max_len:
                self.text += ch

    def draw(self, screen):
        pygame.draw.rect(screen, (20, 20, 40), self.rect, border_radius=6)
        border = (120, 180, 255) if self.active else (90, 90, 110)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)
        cursor = "|" if self.active and (pygame.time.get_ticks() // 500) % 2 else ""
        draw_text(screen, self.text + cursor, 28, (255, 255, 255),
                  (self.rect.x + 12, self.rect.centery), "midleft")
