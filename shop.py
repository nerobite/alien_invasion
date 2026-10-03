import pygame

from button import Button
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, UPGRADES, UPGRADE_ORDER,
                      WEAPONS, WEAPON_ORDER, AMMO, AMMO_ORDER, SHIPS, SHIP_ORDER,
                      compute_stats)
from ui import dim_screen, draw_panel, draw_coins, draw_wrapped
from utils import draw_text, draw_coin

TABS = [("upgrades", "Улучшения"), ("weapon", "Оружие"), ("ammo", "Снаряды"), ("ship", "Корабли")]
ITEM_TABLES = {
    "weapon": (WEAPONS, WEAPON_ORDER),
    "ammo": (AMMO, AMMO_ORDER),
    "ship": (SHIPS, SHIP_ORDER),
}


def upgrade_effect(key, level):
    """Описание действия улучшения на заданном уровне (без учета корпуса)."""
    s = compute_stats({"upgrades": {key: level}})
    return {
        "damage": f"Урон +{level * 20}%",
        "firerate": f"Темп стрельбы +{round((1 / 0.92 ** level - 1) * 100)}%",
        "guns": f"Стволов: +{level}",
        "armor": f"Поглощает +{level * 7}% урона",
        "hull": f"Здоровье +{level * 25}",
        "lives": f"Кораблей: +{level}",
        "engine": f"Скорость +{level * 12}%",
        "regen": f"Ремонт: {s['regen']:.0f} ед./сек",
    }[key]


class ShopScene:
    """Магазин. Открывается только до вылета (меню, подготовка, лобби)
    и в перерыве между уровнями. return_scene — куда вернуться."""

    def __init__(self, app, return_scene):
        self.app = app
        pygame.mouse.set_visible(True)
        self.return_scene = return_scene
        self.tab = "upgrades"
        self.notice = ""
        self.notice_timer = 0
        self.tab_buttons = {key: Button((300 + i * 160, 26, 150, 42), title, 21, (50, 60, 110))
                            for i, (key, title) in enumerate(TABS)}

        self.upgrade_buttons = {}
        for i, key in enumerate(UPGRADE_ORDER):
            card = self._upgrade_card(i)
            self.upgrade_buttons[key] = Button((card.right - 140, card.bottom - 48, 128, 38), "", 22)

        self.item_buttons = {}
        for kind, (_, order) in ITEM_TABLES.items():
            for i, item_id in enumerate(order):
                card = self._item_card(kind, i)
                self.item_buttons[(kind, item_id)] = Button(
                    (card.right - 140, card.bottom - 48, 128, 38), "", 22)
        self.back_button = Button((SCREEN_WIDTH - 230, SCREEN_HEIGHT - 72, 200, 50), "Назад", 26,
                                  (120, 60, 60))

    # ------------------------------------------------------------ раскладка
    @staticmethod
    def _upgrade_card(i):
        return pygame.Rect(30 + (i % 2) * 620, 90 + (i // 2) * 122, 600, 110)

    @staticmethod
    def _item_card(kind, i):
        if kind == "ship":
            return pygame.Rect(30 + i * 247, 90, 232, 430)
        return pygame.Rect(30 + (i % 2) * 620, 90 + (i // 2) * 175, 600, 160)

    # ------------------------------------------------------------ действия
    def _notify(self, text):
        self.notice = text
        self.notice_timer = 2 * FPS

    def _back(self):
        self.app.profile.save()
        self.app.switch(self.return_scene, close=False)
        if hasattr(self.return_scene, "on_resume"):
            self.return_scene.on_resume()

    def handle_event(self, event):
        profile = self.app.profile
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or self.back_button.clicked(event):
            self._back()
            return
        for key, button in self.tab_buttons.items():
            if button.clicked(event):
                self.tab = key
        if self.tab == "upgrades":
            for key, button in self.upgrade_buttons.items():
                if button.clicked(event):
                    price = profile.next_upgrade_price(key)
                    if price is None:
                        self._notify("Достигнут максимальный уровень")
                    elif profile.buy_upgrade(key):
                        self._notify(f"Куплено: {UPGRADES[key]['name']} — ур. {profile.upgrades[key]}")
                    else:
                        self._notify(f"Не хватает монет: нужно еще {price - profile.coins}")
            return
        table, _ = ITEM_TABLES[self.tab]
        for (kind, item_id), button in self.item_buttons.items():
            if kind != self.tab or not button.clicked(event):
                continue
            name = table[item_id]["name"]
            if profile.owns(kind, item_id):
                profile.select_item(kind, item_id)
                self._notify(f"Выбрано: {name}")
            elif profile.buy_item(kind, item_id):
                self._notify(f"Куплено и выбрано: {name}")
            else:
                self._notify(f"Не хватает монет: нужно еще {table[item_id]['price'] - profile.coins}")

    def update(self):
        self.app.starfield.update()
        if self.notice_timer:
            self.notice_timer -= 1

    # ------------------------------------------------------------ отрисовка
    def draw(self, screen):
        self.app.renderer.draw_background(screen, 0)
        self.app.starfield.draw(screen)
        dim_screen(screen, 110)
        profile = self.app.profile
        draw_text(screen, "МАГАЗИН", 48, (255, 215, 60), (30, 20), bold=True)
        for key, button in self.tab_buttons.items():
            button.draw(screen)
            if key == self.tab:
                pygame.draw.rect(screen, (255, 215, 60), button.rect, 3, border_radius=8)
        draw_coins(screen, profile.coins, (SCREEN_WIDTH - 30, 28), 34)

        if self.tab == "upgrades":
            for i, key in enumerate(UPGRADE_ORDER):
                self._draw_upgrade_card(screen, i, key, profile)
        else:
            table, order = ITEM_TABLES[self.tab]
            for i, item_id in enumerate(order):
                self._draw_item_card(screen, self.tab, i, item_id, table[item_id], profile)

        stats = compute_stats(profile.loadout())
        line = (f"{SHIPS[stats['ship']]['name']}: здоровье {stats['max_hp']}   броня {round(stats['armor'] * 100)}%   "
                f"кораблей {stats['lives']}   стволов {stats['guns']}   скорость {stats['speed']:.1f}   "
                f"урон в секунду ≈ {stats['dps']:.1f}")
        draw_text(screen, "Ваш корабль", 20, (150, 150, 190), (30, SCREEN_HEIGHT - 82), bold=True)
        draw_text(screen, line, 19, (255, 255, 255), (30, SCREEN_HEIGHT - 56))
        if self.notice_timer:
            draw_text(screen, self.notice, 22, (255, 230, 140), (30, SCREEN_HEIGHT - 120), bold=True)
        self.back_button.draw(screen)

    @staticmethod
    def _price_button(button, price, coins):
        button.text = f"{price}"
        button.enabled = True
        button.color = (40, 150, 70) if price <= coins else (110, 70, 40)

    def _draw_upgrade_card(self, screen, i, key, profile):
        rect = self._upgrade_card(i)
        button = self.upgrade_buttons[key]
        draw_panel(screen, rect)
        info = UPGRADES[key]
        level = profile.upgrades[key]
        draw_text(screen, info["name"], 24, (255, 255, 255), (rect.x + 14, rect.y + 10), bold=True)
        if level < info["max"]:
            effect = f"{upgrade_effect(key, level)}  →  {upgrade_effect(key, level + 1)}"
        else:
            effect = upgrade_effect(key, level)
        draw_text(screen, effect, 18, (170, 220, 255), (rect.x + 14, rect.y + 42))
        pip_w = min(26, (rect.width - 200) // info["max"])
        for n in range(info["max"]):
            pip = pygame.Rect(rect.x + 14 + n * pip_w, rect.bottom - 30, pip_w - 4, 14)
            pygame.draw.rect(screen, (90, 220, 120) if n < level else (50, 50, 70), pip, border_radius=3)

        price = profile.next_upgrade_price(key)
        if price is None:
            button.text, button.enabled, button.color = "МАКС", False, (60, 60, 70)
        else:
            self._price_button(button, price, profile.coins)
        button.draw(screen)
        if price is not None:
            draw_coin(screen, (button.rect.x + 18, button.rect.centery), 7)

    def _draw_item_card(self, screen, kind, i, item_id, info, profile):
        rect = self._item_card(kind, i)
        button = self.item_buttons[(kind, item_id)]
        selected = profile.selected(kind) == item_id
        draw_panel(screen, rect, (255, 215, 60) if selected else (90, 90, 160))
        if selected:
            pygame.draw.rect(screen, (255, 215, 60), rect, 3, border_radius=12)

        if kind == "ship":
            guns = compute_stats(dict(profile.loadout(), ship=item_id))["guns"]
            image = self.app.renderer.armed_ship(item_id, profile.weapon, guns)
            big = pygame.transform.smoothscale(image, (image.get_width() * 2, image.get_height() * 2))
            screen.blit(big, big.get_rect(center=(rect.centerx, rect.y + 85)))
            draw_text(screen, info["name"], 24, (255, 255, 255), (rect.centerx, rect.y + 160), "midtop", True)
            y = draw_wrapped(screen, info["desc"], 16, (170, 220, 255), (rect.x + 14, rect.y + 192),
                             rect.width - 28)
            stats = [f"Здоровье: {info['hp']}", f"Скорость: {info['speed']:g}",
                     f"Броня: {round(info['armor'] * 100)}%", f"Урон: x{info['damage']:g}",
                     f"Темп стрельбы: x{info['firerate']:g}"]
            if info["guns"]:
                stats.append(f"Стволов: +{info['guns']}")
            if info["lives"]:
                stats.append(f"Кораблей: +{info['lives']}")
            for n, text in enumerate(stats):
                draw_text(screen, text, 16, (210, 210, 210), (rect.x + 14, y + 6 + n * 21))
        else:
            if kind == "weapon":
                number = WEAPON_ORDER.index(item_id) + 1
                title = f"{number}. {info['name']}"
                details = f"Урон {info['damage']:g}  ·  {FPS / info['cooldown']:.1f} выстр./сек"
            else:
                title = info["name"]
                details = "Переключение — клавиша Q"
            # Картинка оружия или снарядов слева
            icons = self.app.renderer.weapon_icons if kind == "weapon" else self.app.renderer.ammo_icons
            icon = icons[item_id]
            frame = pygame.Rect(rect.x + 12, rect.y + 12, 150, rect.height - 24)
            pygame.draw.rect(screen, (28, 28, 58), frame, border_radius=10)
            screen.blit(icon, icon.get_rect(center=frame.center))
            tx = frame.right + 16
            draw_text(screen, title, 26, (255, 255, 255), (tx, rect.y + 12), bold=True)
            draw_text(screen, info["desc"], 18, (170, 220, 255), (tx, rect.y + 52))
            draw_text(screen, details, 16, (200, 200, 200), (tx, rect.y + 80))
            if kind == "weapon":
                draw_text(screen, "Смена в бою: E или 1–4",
                          14, (150, 150, 170), (tx, rect.y + 104))

        if selected:
            button.text, button.enabled, button.color = "Выбрано", False, (60, 60, 70)
        elif profile.owns(kind, item_id):
            button.text, button.enabled, button.color = "Выбрать", True, (40, 110, 190)
        else:
            self._price_button(button, info["price"], profile.coins)
        button.draw(screen)
        if not profile.owns(kind, item_id):
            draw_coin(screen, (button.rect.x + 18, button.rect.centery), 7)

    def on_exit(self):
        self.app.profile.save()
