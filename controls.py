import pygame

from settings import WEAPONS, AMMO, WEAPON_ORDER, AMMO_ORDER

# Схемы управления (выбираются в «Настройках»).
# Клавиши E / Q / 1–4 одинаковы во всех схемах.
CONTROL_SCHEMES = {
    "both": dict(name="Стрелки и WASD", fire_name="Пробел",
                 left=[pygame.K_LEFT, pygame.K_a], right=[pygame.K_RIGHT, pygame.K_d],
                 up=[pygame.K_UP, pygame.K_w], down=[pygame.K_DOWN, pygame.K_s],
                 fire=[pygame.K_SPACE], mouse=False),
    "arrows": dict(name="Стрелки", fire_name="Пробел или Ctrl",
                   left=[pygame.K_LEFT], right=[pygame.K_RIGHT],
                   up=[pygame.K_UP], down=[pygame.K_DOWN],
                   fire=[pygame.K_SPACE, pygame.K_LCTRL, pygame.K_RCTRL], mouse=False),
    "wasd": dict(name="WASD", fire_name="Пробел",
                 left=[pygame.K_a], right=[pygame.K_d],
                 up=[pygame.K_w], down=[pygame.K_s],
                 fire=[pygame.K_SPACE], mouse=False),
    "wasd_mouse": dict(name="WASD + мышь", fire_name="левая кнопка мыши или Пробел",
                       left=[pygame.K_a], right=[pygame.K_d],
                       up=[pygame.K_w], down=[pygame.K_s],
                       fire=[pygame.K_SPACE], mouse=True),
}
CONTROL_ORDER = ["both", "arrows", "wasd", "wasd_mouse"]
WEAPON_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]

NO_INPUT = {"l": 0, "r": 0, "u": 0, "d": 0, "f": 0}


def _next_owned(current, owned, order):
    items = [i for i in order if i in owned]
    if current not in items:
        return items[0]
    return items[(items.index(current) + 1) % len(items)]


class LocalControls:
    """Управление игрока на этом компьютере.

    Нажатия передаются в игровой мир словарем
    {"l","r","u","d","f": 0/1, "w": оружие, "a": снаряды}.
    Выбранные оружие и снаряды сразу запоминаются в профиле.
    """

    def __init__(self, profile):
        self.profile = profile

    @property
    def scheme(self):
        return CONTROL_SCHEMES.get(self.profile.controls, CONTROL_SCHEMES["both"])

    def handle_event(self, event):
        """E — следующее оружие, Q — следующие снаряды, 1–4 — оружие по номеру."""
        if event.type != pygame.KEYDOWN:
            return False
        profile = self.profile
        if event.key == pygame.K_e:
            profile.weapon = _next_owned(profile.weapon, profile.owned_weapons, WEAPON_ORDER)
        elif event.key == pygame.K_q:
            profile.ammo = _next_owned(profile.ammo, profile.owned_ammo, AMMO_ORDER)
        elif event.key in WEAPON_KEYS:
            profile.select_item("weapon", WEAPON_ORDER[WEAPON_KEYS.index(event.key)])
        else:
            return False
        return True

    def read(self):
        keys = pygame.key.get_pressed()
        scheme = self.scheme

        def held(names):
            return int(any(keys[k] for k in scheme[names]))

        fire = held("fire") or (scheme["mouse"] and pygame.mouse.get_pressed()[0])
        return {
            "l": held("left"), "r": held("right"), "u": held("up"), "d": held("down"),
            "f": int(fire or self.profile.autofire),
            "w": self.profile.weapon, "a": self.profile.ammo,
        }

    def hint(self):
        """Подсказка для HUD."""
        return (f"E: {WEAPONS[self.profile.weapon]['name']}   "
                f"Q: {AMMO[self.profile.ammo]['name']}")
