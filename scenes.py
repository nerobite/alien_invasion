import math

import pygame

from button import Button, TextInput
from controls import LocalControls, CONTROL_SCHEMES, CONTROL_ORDER, NO_INPUT
from network import HostServer, HostFinder, ClientConnector, local_ips
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, NET_PORT, PROTOCOL_VERSION, FPS,
                      PLAYER_COLORS, WORLDS, DIFFICULTIES, LEVELS_PER_WORLD, SHIPS,
                      WEAPONS, AMMO, compute_stats, world_of_level)
from shop import ShopScene
from ui import CENTER_X, MissionPanel, dim_screen, draw_panel, draw_coins
from utils import draw_text
from world import GameWorld


class Scene:
    """Базовый экран игры."""

    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self):
        self.app.starfield.update()

    def draw(self, screen):
        pass

    def draw_backdrop(self, screen, world_index=0):
        self.app.renderer.draw_background(screen, world_index)
        self.app.starfield.draw(screen)

    def on_exit(self):
        """Вызывается, когда экран закрывается навсегда."""


def key_pressed(event, *keys):
    return event.type == pygame.KEYDOWN and event.key in keys


# ======================================================================= меню
class MenuScene(Scene):
    def __init__(self, app, message=""):
        super().__init__(app)
        pygame.mouse.set_visible(True)
        self.message = message
        labels = [("Играть", (40, 160, 70)),
                  ("Магазин", (190, 140, 20)),
                  ("Создать игру по сети", (40, 110, 190)),
                  ("Подключиться к игре", (40, 110, 190)),
                  ("Настройки", (90, 90, 130)),
                  ("Выход", (150, 50, 50))]
        self.buttons = [Button((CENTER_X - 180, 250 + i * 64, 360, 52), text, 27, color)
                        for i, (text, color) in enumerate(labels)]

    def handle_event(self, event):
        play, shop, host, join, options, leave = self.buttons
        if play.clicked(event) or key_pressed(event, pygame.K_RETURN):
            self.app.switch(BriefingScene(self.app))
        elif shop.clicked(event):
            self.app.switch(ShopScene(self.app, MenuScene(self.app)))
        elif host.clicked(event):
            self.app.switch(LobbyScene(self.app))
        elif join.clicked(event):
            self.app.switch(JoinScene(self.app))
        elif options.clicked(event):
            self.app.switch(SettingsScene(self.app))
        elif leave.clicked(event):
            self.app.quit()

    def draw(self, screen):
        self.draw_backdrop(screen)
        renderer = self.app.renderer
        t = pygame.time.get_ticks() / 1000
        # Декоративный строй пришельцев
        kinds = ("scout", "soldier", "sniper", "kamikaze", "tank", "bomber", "splitter")
        for i, kind in enumerate(kinds):
            image = renderer.alien_images[kind]
            x = CENTER_X - 300 + i * 100
            y = 195 + 6 * math.sin(t * 2 + i)
            screen.blit(image, image.get_rect(center=(x, y)))

        draw_text(screen, "ALIEN INVASION", 84, (40, 40, 90), (CENTER_X + 4, 104), "center", True)
        draw_text(screen, "ALIEN INVASION", 84, (120, 255, 160), (CENTER_X, 100), "center", True)
        for button in self.buttons:
            button.draw(screen)

        profile = self.app.profile
        draw_coins(screen, profile.coins, (SCREEN_WIDTH - 24, 20))
        draw_text(screen, f"Рекорд: {profile.best_score:,}".replace(",", " "), 24,
                  (200, 200, 200), (24, 22), bold=True)
        if self.message:
            draw_text(screen, self.message, 24, (255, 140, 120), (CENTER_X, 650), "center")
        scheme = CONTROL_SCHEMES.get(profile.controls, CONTROL_SCHEMES["both"])
        draw_text(screen, f"Полет: {scheme['name']}   Огонь: {scheme['fire_name']}   E — оружие   "
                          f"Q — снаряды   ESC — пауза   F11 — окно",
                  17, (140, 140, 170), (CENTER_X, SCREEN_HEIGHT - 22), "center")


# =================================================================== настройки
class SettingsScene(Scene):
    """Выбор схемы управления и автоогня."""

    def __init__(self, app):
        super().__init__(app)
        pygame.mouse.set_visible(True)
        self.scheme_buttons = [Button((CENTER_X - 300, 170 + i * 66, 600, 54),
                                      CONTROL_SCHEMES[key]["name"], 24, (50, 70, 120))
                               for i, key in enumerate(CONTROL_ORDER)]
        self.autofire_button = Button((CENTER_X - 300, 450, 600, 54), "", 24, (60, 90, 60))
        self.back_button = Button((CENTER_X - 100, SCREEN_HEIGHT - 80, 200, 50), "Назад", 26, (150, 50, 50))

    def handle_event(self, event):
        profile = self.app.profile
        if self.back_button.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
            profile.save()
            self.app.switch(MenuScene(self.app))
        for key, button in zip(CONTROL_ORDER, self.scheme_buttons):
            if button.clicked(event):
                profile.controls = key
        if self.autofire_button.clicked(event):
            profile.autofire = not profile.autofire

    def draw(self, screen):
        self.draw_backdrop(screen)
        draw_panel(screen, pygame.Rect(CENTER_X - 340, 60, 680, 600))
        draw_text(screen, "НАСТРОЙКИ", 44, (120, 200, 255), (CENTER_X, 100), "center", True)
        draw_text(screen, "Схема управления", 22, (200, 200, 255), (CENTER_X - 300, 140), bold=True)
        profile = self.app.profile
        for key, button in zip(CONTROL_ORDER, self.scheme_buttons):
            scheme = CONTROL_SCHEMES[key]
            button.text = f"{scheme['name']}  ·  огонь: {scheme['fire_name']}"
            button.size = 20
            button.draw(screen)
            if key == profile.controls:
                pygame.draw.rect(screen, (255, 215, 60), button.rect, 3, border_radius=8)
        self.autofire_button.text = f"Автоогонь: {'ВКЛ' if profile.autofire else 'ВЫКЛ'}"
        self.autofire_button.color = (40, 150, 70) if profile.autofire else (90, 70, 70)
        self.autofire_button.draw(screen)
        hints = ["E — следующее оружие,  1–4 — оружие по номеру",
                 "Q — следующий тип снарядов",
                 "ESC или P — пауза,  F11 — окно / полный экран"]
        for i, text in enumerate(hints):
            draw_text(screen, text, 19, (200, 200, 200), (CENTER_X - 300, 525 + i * 26))
        self.back_button.draw(screen)


# ============================================================ подготовка к вылету
class BriefingScene(Scene):
    """Перед одиночной игрой: сложность, стартовый мир, корабль, магазин."""

    def __init__(self, app):
        super().__init__(app)
        pygame.mouse.set_visible(True)
        self.panel = MissionPanel(app.profile, 60, 110, 640)
        self.shop_button = Button((790, 520, 190, 54), "Магазин", 26, (190, 140, 20))
        self.start_button = Button((1000, 520, 220, 54), "В бой!", 28)
        self.back_button = Button((60, SCREEN_HEIGHT - 80, 200, 50), "Назад", 26, (150, 50, 50))

    def handle_event(self, event):
        if self.back_button.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
            self.app.switch(MenuScene(self.app))
        elif self.shop_button.clicked(event):
            self.app.switch(ShopScene(self.app, self), close=False)
        elif self.start_button.clicked(event) or key_pressed(event, pygame.K_RETURN):
            self.app.profile.save()
            self.app.switch(GameScene(self.app))
        else:
            self.panel.handle_event(event)

    def on_resume(self):
        pygame.mouse.set_visible(True)

    def draw(self, screen):
        self.draw_backdrop(screen, self.panel.world)
        draw_panel(screen, pygame.Rect(40, 40, SCREEN_WIDTH - 80, 560))
        draw_text(screen, "ПОДГОТОВКА К ВЫЛЕТУ", 36, (120, 200, 255), (60, 58), bold=True)
        self.panel.draw(screen)
        draw_loadout(screen, self.app, 790, 110)
        draw_text(screen, f"Рекорд на этой сложности: "
                          f"{self.app.profile.high_scores[self.panel.difficulty]:,}".replace(",", " "),
                  18, (180, 180, 180), (60, 560))
        self.shop_button.draw(screen)
        self.start_button.draw(screen)
        self.back_button.draw(screen)


def draw_loadout(screen, app, x, y):
    """Карточка текущего корабля: картинка, оружие, снаряды и характеристики."""
    profile = app.profile
    stats = compute_stats(profile.loadout())
    image = app.renderer.armed_ship(profile.ship, profile.weapon, stats["guns"])
    big = pygame.transform.smoothscale(image, (image.get_width() * 2, image.get_height() * 2))
    screen.blit(big, big.get_rect(center=(x + 80, y + 80)))
    draw_text(screen, SHIPS[profile.ship]["name"], 28, (255, 255, 255), (x + 180, y + 10), bold=True)
    draw_text(screen, f"Оружие: {WEAPONS[profile.weapon]['name']}", 20, (170, 220, 255), (x + 180, y + 50))
    draw_text(screen, f"Снаряды: {AMMO[profile.ammo]['name']}", 20, (170, 220, 255), (x + 180, y + 76))
    lines = [f"Здоровье: {stats['max_hp']}", f"Броня: {round(stats['armor'] * 100)}%",
             f"Кораблей: {stats['lives']}", f"Стволов: {stats['guns']}",
             f"Скорость: {stats['speed']:.1f}", f"Урон в секунду ≈ {stats['dps']:.1f}"]
    for i, text in enumerate(lines):
        draw_text(screen, text, 19, (220, 220, 220), (x + 10 + (i % 2) * 210, y + 180 + (i // 2) * 30))
    draw_coins(screen, profile.coins, (x + 400, y + 290), 28)


# ======================================================================= игра
def next_level_text(level):
    """Что ждет на следующем уровне."""
    nxt = level + 1
    world = WORLDS[world_of_level(nxt)]
    in_world = (nxt - 1) % LEVELS_PER_WORLD + 1
    text = f"Далее: {world['name']}, уровень {in_world}"
    if in_world == 1:
        text += " — НОВЫЙ МИР!"
    elif in_world == LEVELS_PER_WORLD:
        text += " — БОСС!"
    return text


def draw_intermission(screen, snap, local_index, buttons, status=""):
    """Перерыв между уровнями: итоги и кнопки (магазин, дальше)."""
    dim_screen(screen, 140)
    rect = pygame.Rect(CENTER_X - 330, 150, 660, 400)
    draw_panel(screen, rect)
    draw_text(screen, f"УРОВЕНЬ {snap['lvl']} ПРОЙДЕН", 46, (120, 255, 160), (CENTER_X, 195), "center", True)
    draw_text(screen, next_level_text(snap["lvl"]), 22, (200, 200, 255), (CENTER_X, 240), "center")
    for i, p in enumerate(snap["p"]):
        y = 285 + i * 40
        name = "Вы" if i == local_index or len(snap["p"]) == 1 else "Напарник"
        draw_text(screen, f"{name}: очки {p[7]:,}".replace(",", " "), 22, PLAYER_COLORS[i],
                  (rect.x + 40, y), bold=True)
        draw_coins(screen, p[8], (rect.right - 40, y), 24)
    draw_text(screen, "Магазин доступен только сейчас — между уровнями", 18, (180, 180, 200),
              (CENTER_X, 380), "center")
    if status:
        draw_text(screen, status, 20, (255, 215, 120), (CENTER_X, 410), "center", True)
    for button in buttons:
        button.draw(screen)


def draw_results(screen, snap, local_index, buttons, new_record=False, note=""):
    """Итоги игры: очки, уничтоженные пришельцы и монеты каждого игрока."""
    dim_screen(screen)
    rect = pygame.Rect(CENTER_X - 330, 130, 660, 430)
    draw_panel(screen, rect)
    draw_text(screen, "ИГРА ОКОНЧЕНА", 56, (255, 90, 90), (CENTER_X, 180), "center", True)
    world = WORLDS[snap["w"]]
    draw_text(screen, f"{world['name']}, уровень {(snap['lvl'] - 1) % LEVELS_PER_WORLD + 1} · "
                      f"{DIFFICULTIES[snap['df']]['name']}", 24, (200, 200, 255), (CENTER_X, 228), "center")
    players = snap["p"]
    for i, p in enumerate(players):
        y = 270 + i * 80
        column_x = rect.x + 40
        name = "Ваш результат" if (i == local_index or len(players) == 1) else "Напарник"
        draw_text(screen, name, 24, PLAYER_COLORS[i], (column_x, y), bold=True)
        draw_text(screen, f"Очки: {p[7]:,}".replace(",", " ") + f"    Сбито пришельцев: {p[10]}",
                  22, (255, 255, 255), (column_x, y + 32))
        draw_coins(screen, p[8], (rect.right - 40, y + 14), 28)
    if new_record:
        draw_text(screen, "НОВЫЙ РЕКОРД!", 30, (255, 215, 60), (CENTER_X, 445), "center", True)
    if note:
        draw_text(screen, note, 20, (180, 180, 200), (CENTER_X, 540), "center")
    for button in buttons:
        button.draw(screen)


class GameScene(Scene):
    """Одиночная игра или игра хоста (тогда server — HostServer)."""

    def __init__(self, app, server=None, guest_loadout=None):
        super().__init__(app)
        self.server = server
        self.guest_loadout = guest_loadout
        self.guest_input = dict(NO_INPUT)
        self.controls = LocalControls(app.profile)
        self.pause_buttons = [Button((CENTER_X - 150, 300 + i * 70, 300, 54), text, 26, color)
                              for i, (text, color) in enumerate([
                                  ("Продолжить", (40, 160, 70)),
                                  ("Выйти в меню", (150, 50, 50))])]
        self.over_buttons = [Button((CENTER_X - 260, 470, 240, 54), "Еще раз", 26),
                             Button((CENTER_X + 20, 470, 240, 54), "В меню", 26, (150, 50, 50))]
        self.break_buttons = [Button((CENTER_X - 310, 450, 190, 54), "Магазин", 24, (190, 140, 20)),
                              Button((CENTER_X - 105, 450, 250, 54), "Следующий уровень", 22),
                              Button((CENTER_X + 160, 450, 150, 54), "В меню", 24, (150, 50, 50))]
        self.new_game()

    @property
    def networked(self):
        return self.server is not None

    @property
    def guest_present(self):
        players = self.world.players
        return self.networked and len(players) > 1 and players[1].connected

    def new_game(self):
        profile = self.app.profile
        loadouts = [profile.loadout()]
        if self.networked and self.server.connected and self.guest_loadout:
            loadouts.append(self.guest_loadout)
            self.server.send({"t": "start", "you": 1})
        start_world = min(profile.start_world, profile.unlocked_world)
        self.world = GameWorld(loadouts, profile.difficulty, start_world)
        self.credited = 0           # монеты, уже зачисленные в профиль
        self.last_level = self.world.level
        self.guest_ready = False
        self.paused = False
        self.results_saved = False
        self.message = ""
        self.message_timer = 0
        self.frame = 0
        self.app.renderer.reset_effects()
        self.snap = self.world.snapshot()
        pygame.mouse.set_visible(False)

    def on_resume(self):
        """Возврат из магазина (только в перерыве): применяем покупки."""
        self.world.players[0].apply_loadout(self.app.profile.loadout())
        pygame.mouse.set_visible(True)

    def _set_paused(self, paused):
        self.paused = paused
        pygame.mouse.set_visible(paused)

    def _can_continue(self):
        return not self.guest_present or self.guest_ready

    def handle_event(self, event):
        world = self.world
        if world.game_over:
            again, menu = self.over_buttons
            if again.clicked(event) or key_pressed(event, pygame.K_RETURN):
                self.new_game()
            elif menu.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
                self.app.switch(MenuScene(self.app))
            return
        if world.intermission:
            shop, go, menu = self.break_buttons
            if shop.clicked(event):
                self._credit_coins()
                self.app.switch(ShopScene(self.app, self), close=False)
            elif (go.clicked(event) or key_pressed(event, pygame.K_RETURN)) and self._can_continue():
                world.next_level()
                self.guest_ready = False
                pygame.mouse.set_visible(False)
            elif menu.clicked(event):
                self.app.switch(MenuScene(self.app))
            return
        if key_pressed(event, pygame.K_ESCAPE, pygame.K_p):
            self._set_paused(not self.paused)
            return
        if self.paused:
            resume, menu = self.pause_buttons
            if resume.clicked(event):
                self._set_paused(False)
            elif menu.clicked(event):
                self.app.switch(MenuScene(self.app))
        else:
            self.controls.handle_event(event)

    def update(self):
        super().update()
        self.frame += 1
        if self.networked:
            self._process_network()

        world = self.world
        if not self.paused:
            world.step([self.controls.read(), self.guest_input])
        self.snap = world.snapshot()
        self.app.renderer.process_events(self.snap["ev"], 0)
        if self.networked and self.server.connected:
            self.snap["ps"] = int(self.paused)
            self.snap["gr"] = int(self.guest_ready)
            # В перерыве картинка не меняется — шлем реже
            if not world.intermission or self.frame % 10 == 0 or self.snap["ev"]:
                self.server.send(self.snap)

        self._credit_coins()
        self.break_buttons[1].enabled = self._can_continue()
        if world.intermission:
            pygame.mouse.set_visible(True)
        if world.level != self.last_level:
            self.last_level = world.level
            self.app.profile.unlock_world(world.world_index)
            self.app.profile.save()
        if self.message_timer:
            self.message_timer -= 1
        if world.game_over and not self.results_saved:
            self._save_results()

    def _process_network(self):
        world = self.world
        for message in self.server.receive_all():
            kind = message.get("t")
            if kind == "in":
                self.guest_input = {k: int(message.get(k, 0)) for k in NO_INPUT}
                self.guest_input["w"] = message.get("w")
                self.guest_input["a"] = message.get("a")
            elif kind in ("loadout", "ready") and world.intermission and len(world.players) > 1:
                # Покупки напарника применяются только в перерыве
                self.guest_loadout = message.get("loadout", self.guest_loadout)
                world.players[1].apply_loadout(self.guest_loadout)
                if kind == "ready":
                    self.guest_ready = bool(message.get("v", 1))
            elif kind == "bye":
                self.server.conn.close()
        if self.guest_present and not self.server.connected:
            world.disconnect_player(1)
            self.guest_input = dict(NO_INPUT)
            self.message = "Напарник отключился"
            self.message_timer = 4 * FPS

    def _credit_coins(self):
        """Заработанные монеты сразу зачисляются в профиль."""
        earned = self.world.players[0].coins
        self.app.profile.coins += earned - self.credited
        self.credited = earned

    def _save_results(self):
        self.results_saved = True
        profile = self.app.profile
        difficulty = self.world.difficulty
        self.new_record = (not self.networked and self.world.score > profile.high_scores[difficulty])
        if self.new_record:
            profile.high_scores[difficulty] = self.world.score
        profile.save()
        pygame.mouse.set_visible(True)

    def draw(self, screen):
        self.draw_backdrop(screen, self.snap["w"])
        high = None if self.networked else self.app.profile.high_scores[self.world.difficulty]
        self.app.renderer.draw_world(screen, self.snap, 0, high, self.controls.hint())
        if self.message_timer:
            draw_text(screen, self.message, 26, (255, 150, 120), (CENTER_X, 90), "center", True)

        if self.world.game_over:
            draw_results(screen, self.snap, 0, self.over_buttons, new_record=self.new_record)
        elif self.world.intermission:
            status = ""
            if self.guest_present:
                status = "Напарник готов!" if self.guest_ready else "Ждем, пока напарник нажмет «Готов»..."
            draw_intermission(screen, self.snap, 0, self.break_buttons, status)
        elif self.paused:
            dim_screen(screen)
            draw_text(screen, "ПАУЗА", 64, (255, 255, 255), (CENTER_X, 200), "center", True)
            draw_text(screen, "Магазин откроется в перерыве между уровнями", 20,
                      (180, 180, 200), (CENTER_X, 255), "center")
            for button in self.pause_buttons:
                button.draw(screen)

    def on_exit(self):
        self._credit_coins()
        self.app.profile.save()
        if self.server:
            self.server.close()


# ==================================================================== сеть: хост
class LobbyScene(Scene):
    """Хост выбирает сложность и мир и ждет подключения напарника."""

    def __init__(self, app):
        super().__init__(app)
        pygame.mouse.set_visible(True)
        self.error = ""
        self.server = None
        try:
            self.server = HostServer()
        except OSError as e:
            self.error = f"Не удалось открыть порт {NET_PORT}: {e}"
        self.ips = local_ips()
        self.guest_loadout = None
        self.panel = MissionPanel(app.profile, 60, 110, 640)
        self.shop_button = Button((760, 560, 140, 54), "Магазин", 22, (190, 140, 20))
        self.start_button = Button((915, 560, 180, 54), "Начать игру", 22)
        self.back_button = Button((1110, 560, 120, 54), "Назад", 22, (150, 50, 50))

    def _send_mission(self):
        if self.server and self.server.connected:
            self.server.send({"t": "lobby", "df": self.panel.difficulty, "w": self.panel.world})

    def handle_event(self, event):
        if self.back_button.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
            self.app.switch(MenuScene(self.app))
        elif self.shop_button.clicked(event):
            self.app.switch(ShopScene(self.app, self), close=False)
        elif self.start_button.enabled and (self.start_button.clicked(event)
                                            or key_pressed(event, pygame.K_RETURN)):
            self.app.profile.save()
            server, self.server = self.server, None   # сервер переходит к игре
            self.app.switch(GameScene(self.app, server, self.guest_loadout))
        elif self.panel.handle_event(event):
            self._send_mission()

    def on_resume(self):
        pygame.mouse.set_visible(True)

    def update(self):
        super().update()
        if not self.server:
            return
        for message in self.server.receive_all():
            if message.get("t") == "hello":
                if message.get("ver") == PROTOCOL_VERSION:
                    self.guest_loadout = message.get("loadout", {})
                    self.server.send({"t": "welcome"})
                    self._send_mission()
                else:
                    self.server.send({"t": "bye", "reason": "У хоста другая версия игры"})
        if not self.server.connected:
            self.guest_loadout = None
        self.start_button.enabled = self.guest_loadout is not None

    def draw(self, screen):
        self.draw_backdrop(screen, self.panel.world)
        draw_panel(screen, pygame.Rect(40, 40, SCREEN_WIDTH - 80, 600))
        draw_text(screen, "ИГРА ПО ЛОКАЛЬНОЙ СЕТИ", 36, (120, 200, 255), (60, 58), bold=True)
        self.panel.draw(screen)

        x = 760
        if self.error:
            draw_text(screen, self.error, 18, (255, 120, 120), (x, 120))
        else:
            draw_text(screen, "Напарник выбирает «Подключиться»", 20, (220, 220, 220), (x, 110))
            draw_text(screen, "и находит игру в списке или вводит адрес:", 20, (220, 220, 220), (x, 136))
            for i, ip in enumerate(self.ips[:3]):
                draw_text(screen, ip, 34 if i == 0 else 20, (255, 255, 255), (x, 175 + i * 30 + (14 if i else 0)), bold=True)
            if self.guest_loadout is not None:
                ship = SHIPS.get(self.guest_loadout.get("ship"), SHIPS["wanderer"])["name"]
                status, color = "Игрок 2 подключился!", (120, 255, 140)
                draw_text(screen, f"Корабль напарника: {ship}", 20, (220, 220, 220), (x, 345))
            else:
                dots = "." * (pygame.time.get_ticks() // 400 % 4)
                status, color = "Ожидание напарника" + dots, (255, 215, 120)
            draw_text(screen, status, 26, color, (x, 305), bold=True)
            draw_text(screen, "Сложность и мир выбирает хост.", 18, (180, 180, 200), (x, 400))
            draw_text(screen, "Каждый играет своим кораблем", 18, (180, 180, 200), (x, 424))
            draw_text(screen, "и получает монеты за свои сбитые цели.", 18, (180, 180, 200), (x, 448))
        self.shop_button.draw(screen)
        self.start_button.draw(screen)
        self.back_button.draw(screen)

    def on_exit(self):
        if self.server:
            self.server.close()


# ================================================================ сеть: клиент
class JoinScene(Scene):
    """Поиск игры в сети и подключение к хосту."""

    def __init__(self, app):
        super().__init__(app)
        pygame.mouse.set_visible(True)
        self.finder = HostFinder()
        self.ip_input = TextInput((CENTER_X - 260, 470, 330, 50), "192.168.")
        self.connect_button = Button((CENTER_X + 85, 470, 175, 50), "Подключиться", 22, (40, 110, 190))
        self.shop_button = Button((CENTER_X - 230, 615, 200, 50), "Магазин", 24, (190, 140, 20))
        self.back_button = Button((CENTER_X + 30, 615, 200, 50), "Назад", 26, (150, 50, 50))
        self.host_buttons = []
        self.connector = None
        self.conn = None
        self.mission = None
        self.status = ""
        self.status_color = (255, 255, 255)

    def _connect(self, ip):
        if self.connector or self.conn:
            return
        self.connector = ClientConnector(ip.strip())
        self._set_status(f"Подключение к {ip}...", (255, 215, 120))

    def _set_status(self, text, color):
        self.status, self.status_color = text, color

    def _send_hello(self):
        self.conn.send({"t": "hello", "ver": PROTOCOL_VERSION, "loadout": self.app.profile.loadout()})

    def _drop(self, reason):
        if self.conn:
            self.conn.close()
        self.conn = None
        self.mission = None
        self._set_status(reason, (255, 120, 120))

    def on_resume(self):
        """Возврат из магазина: сообщаем хосту новое снаряжение."""
        pygame.mouse.set_visible(True)
        if self.conn:
            self._send_hello()

    def handle_event(self, event):
        if self.back_button.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
            self.app.switch(MenuScene(self.app))
            return
        if self.shop_button.clicked(event):
            self.app.switch(ShopScene(self.app, self), close=False)
            return
        self.ip_input.handle_event(event)
        if self.connect_button.clicked(event) or key_pressed(event, pygame.K_RETURN):
            self._connect(self.ip_input.text)
        for button, ip in self.host_buttons:
            if button.clicked(event):
                self.ip_input.text = ip
                self._connect(ip)

    def update(self):
        super().update()
        hosts = self.finder.active_hosts()
        self.host_buttons = [
            (Button((CENTER_X - 260, 220 + i * 56, 520, 46),
                    f"{name} ({ip})" + ("  — занято" if busy else ""), 22,
                    (60, 60, 90) if busy else (40, 110, 190), enabled=not busy), ip)
            for i, (ip, name, port, busy) in enumerate(hosts[:4])]

        if self.connector and self.connector.done:
            if self.connector.conn:
                self.conn = self.connector.conn
                self._send_hello()
                self._set_status("Соединение установлено...", (255, 215, 120))
            else:
                self._set_status(f"Не удалось подключиться: {self.connector.error}", (255, 120, 120))
            self.connector = None

        if not self.conn:
            return
        messages = self.conn.receive_all()
        for i, message in enumerate(messages):
            kind = message.get("t")
            if kind == "welcome":
                self._set_status("Подключено! Ждем, пока хост начнет игру...", (120, 255, 140))
            elif kind == "lobby":
                self.mission = message
            elif kind == "start":
                conn, self.conn = self.conn, None   # соединение переходит к игре
                self.app.switch(ClientGameScene(self.app, conn, message.get("you", 1), messages[i + 1:]))
                return
            elif kind == "bye":
                self._drop(message.get("reason", "Хост закрыл игру"))
                return
        if not self.conn.alive:
            self._drop("Соединение потеряно")

    def draw(self, screen):
        self.draw_backdrop(screen)
        draw_panel(screen, pygame.Rect(CENTER_X - 320, 90, 640, 600))
        draw_text(screen, "ПОДКЛЮЧЕНИЕ К ИГРЕ", 40, (120, 200, 255), (CENTER_X, 135), "center", True)
        draw_text(screen, "Найденные игры в локальной сети:", 22, (220, 220, 220), (CENTER_X, 185), "center")
        if not self.host_buttons:
            dots = "." * (pygame.time.get_ticks() // 400 % 4)
            draw_text(screen, "Поиск" + dots, 22, (150, 150, 170), (CENTER_X, 250), "center")
        for button, _ in self.host_buttons:
            button.draw(screen)
        draw_text(screen, "Или введите IP-адрес хоста:", 22, (220, 220, 220), (CENTER_X - 260, 438))
        self.ip_input.draw(screen)
        self.connect_button.draw(screen)
        if self.status:
            draw_text(screen, self.status, 22, self.status_color, (CENTER_X, 545), "center", True)
        if self.mission:
            diff = DIFFICULTIES.get(self.mission.get("df"), DIFFICULTIES["normal"])
            world = WORLDS[min(int(self.mission.get("w", 0)), len(WORLDS) - 1)]
            draw_text(screen, f"Хост выбрал: {diff['name']}, {world['name']}", 20,
                      diff["color"], (CENTER_X, 578), "center", True)
        self.shop_button.draw(screen)
        self.back_button.draw(screen)

    def on_exit(self):
        self.finder.close()
        if self.conn:
            self.conn.send({"t": "bye"})
            self.conn.close()


class ClientGameScene(Scene):
    """Игра на стороне клиента: шлет нажатия, рисует присланный хостом мир."""

    def __init__(self, app, conn, index, pending=()):
        super().__init__(app)
        self.conn = conn
        self.index = index
        self.controls = LocalControls(app.profile)
        self.menu_open = False
        self.host_left = ""
        self.leave_button = Button((CENTER_X - 130, 330, 260, 54), "Покинуть игру", 26, (150, 50, 50))
        self.resume_button = Button((CENTER_X - 130, 260, 260, 54), "Продолжить", 26)
        self.menu_button = Button((CENTER_X - 120, 470, 240, 54), "В меню", 26, (150, 50, 50))
        self.break_buttons = [Button((CENTER_X - 310, 450, 190, 54), "Магазин", 24, (190, 140, 20)),
                              Button((CENTER_X - 105, 450, 250, 54), "Готов!", 24),
                              Button((CENTER_X + 160, 450, 150, 54), "Выйти", 24, (150, 50, 50))]
        self._start_round()
        self._handle_messages(list(pending))

    def _start_round(self):
        self.snap = None
        self.credited = 0
        self.ready = False
        self.last_level = None
        self.app.renderer.reset_effects()
        pygame.mouse.set_visible(False)

    @property
    def game_over(self):
        return self.snap is not None and self.snap["go"]

    @property
    def intermission(self):
        return self.snap is not None and self.snap.get("im")

    def on_resume(self):
        """Возврат из магазина: хост применит покупки к нашему кораблю."""
        pygame.mouse.set_visible(True)
        self.conn.send({"t": "loadout", "loadout": self.app.profile.loadout()})

    def handle_event(self, event):
        if self.host_left or self.game_over:
            if self.menu_button.clicked(event) or key_pressed(event, pygame.K_ESCAPE):
                self.app.switch(MenuScene(self.app))
            return
        if self.intermission:
            shop, ready, leave = self.break_buttons
            if shop.clicked(event) and not self.ready:
                self._credit_coins()
                self.app.switch(ShopScene(self.app, self), close=False)
            elif ready.clicked(event) or key_pressed(event, pygame.K_RETURN):
                self.ready = not self.ready
                self.conn.send({"t": "ready", "v": int(self.ready),
                                "loadout": self.app.profile.loadout()})
            elif leave.clicked(event):
                self.app.switch(MenuScene(self.app))
            return
        if key_pressed(event, pygame.K_ESCAPE):
            self.menu_open = not self.menu_open
            pygame.mouse.set_visible(self.menu_open)
        elif self.menu_open:
            if self.resume_button.clicked(event):
                self.menu_open = False
                pygame.mouse.set_visible(False)
            elif self.leave_button.clicked(event):
                self.app.switch(MenuScene(self.app))
        else:
            self.controls.handle_event(event)

    def _handle_messages(self, messages):
        for message in messages:
            kind = message.get("t")
            if kind == "s":
                self.snap = message
                self.app.renderer.process_events(message["ev"], self.index)
            elif kind == "start":
                self._credit_coins()
                self.index = message.get("you", self.index)
                self._start_round()
            elif kind == "bye":
                self.host_left = "Хост завершил игру"

    def update(self):
        super().update()
        if self.host_left:
            return
        self._handle_messages(self.conn.receive_all())
        if not self.conn.alive and not self.host_left:
            self.host_left = "Соединение с хостом потеряно"
        if self.host_left:
            pygame.mouse.set_visible(True)
            self.app.profile.save()
            return

        busy = self.menu_open or self.game_over or self.intermission
        inp = dict(NO_INPUT, w=self.app.profile.weapon, a=self.app.profile.ammo) if busy \
            else self.controls.read()
        self.conn.send(dict(inp, t="in"))
        self._credit_coins()

        if self.snap is not None:
            if self.snap["lvl"] != self.last_level:
                self.last_level = self.snap["lvl"]
                self.ready = False
                self.app.profile.unlock_world(self.snap["w"])
                self.app.profile.save()
            self.break_buttons[1].text = "Не готов" if self.ready else "Готов!"
            self.break_buttons[0].enabled = not self.ready
            if self.game_over or self.intermission:
                pygame.mouse.set_visible(True)
            elif not self.menu_open:
                pygame.mouse.set_visible(False)

    def _credit_coins(self):
        if self.snap is None or self.index >= len(self.snap["p"]):
            return
        earned = self.snap["p"][self.index][8]
        if earned > self.credited:
            self.app.profile.coins += earned - self.credited
            self.credited = earned

    def draw(self, screen):
        if self.snap is None:
            self.draw_backdrop(screen)
            draw_text(screen, "Ожидание данных от хоста...", 30, (255, 255, 255),
                      (CENTER_X, SCREEN_HEIGHT // 2), "center", True)
        else:
            self.draw_backdrop(screen, self.snap["w"])
            self.app.renderer.draw_world(screen, self.snap, self.index, hint=self.controls.hint())
            if self.snap.get("ps") and not self.snap["go"]:
                draw_text(screen, "Хост поставил игру на паузу", 30, (255, 255, 255),
                          (CENTER_X, 160), "center", True)

        if self.host_left:
            dim_screen(screen)
            draw_text(screen, self.host_left, 36, (255, 140, 120), (CENTER_X, 300), "center", True)
            draw_coins(screen, self.credited, (CENTER_X + 30, 370), 30, "center")
            self.menu_button.draw(screen)
        elif self.game_over:
            draw_results(screen, self.snap, self.index, [self.menu_button],
                         note="Хост может начать новую игру — подождите или выйдите в меню")
        elif self.intermission:
            status = "Вы готовы. Ждем, пока хост начнет уровень..." if self.ready \
                else "Загляните в магазин и нажмите «Готов!»"
            draw_intermission(screen, self.snap, self.index, self.break_buttons, status)
        elif self.menu_open:
            dim_screen(screen)
            draw_text(screen, "Игра продолжается!", 40, (255, 255, 255), (CENTER_X, 190), "center", True)
            self.resume_button.draw(screen)
            self.leave_button.draw(screen)

    def on_exit(self):
        self._credit_coins()
        self.app.profile.save()
        self.conn.send({"t": "bye"})
        self.conn.close()
