"""Константы и таблицы баланса игры Alien Invasion."""

# Логическое разрешение. Вся игра считается в нем, а на реальный экран
# картинка масштабируется (pygame.SCALED) — поэтому у обоих игроков
# в сетевой игре одинаковое поле, независимо от их мониторов.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
BG_COLOR = (0, 0, 0)

# Сеть
NET_PORT = 50555          # TCP: игровой обмен
DISCOVERY_PORT = 50556    # UDP: поиск игр в локальной сети
PROTOCOL_VERSION = 2

# Игроки
PLAYER_COLORS = [(90, 200, 255), (255, 170, 60)]
PLAYER_NAMES = ["Игрок 1", "Игрок 2"]
# Корабль может летать только в нижней части экрана
SHIP_MIN_Y = int(SCREEN_HEIGHT * 0.45)

# Расположение стволов: (смещение по x, угол отклонения в градусах)
GUN_LAYOUTS = {
    1: [(0, 0)],
    2: [(-12, 0), (12, 0)],
    3: [(-15, -6), (0, 0), (15, 6)],
    4: [(-19, -9), (-7, -2), (7, 2), (19, 9)],
    5: [(-21, -13), (-11, -6), (0, 0), (11, 6), (21, 13)],
    6: [(-24, -16), (-15, -9), (-6, -2), (6, 2), (15, 9), (24, 16)],
}
MAX_GUNS = 6

# Формация пришельцев
FORMATION_TOP = 95
SLOT_W, SLOT_H = 76, 50
FLEET_DROP = 14

# ------------------------------------------------------------------ миры
# Каждый мир — LEVELS_PER_WORLD уровней, последний из них — босс.
# enemies — веса типов пришельцев; на первых уровнях мира доступны
# только первые типы из списка. meteors — метеоритов примерно за 10 секунд.
LEVELS_PER_WORLD = 5
WORLDS = [
    dict(name="Орбита Земли", bg=(2, 4, 16), nebula=[(40, 70, 170), (20, 50, 110)],
         enemies={"scout": 10, "soldier": 5, "kamikaze": 3, "tank": 2},
         boss="mothership", meteors=0.5),
    dict(name="Пояс астероидов", bg=(12, 7, 4), nebula=[(140, 85, 40), (90, 55, 30)],
         enemies={"scout": 6, "bomber": 4, "soldier": 5, "tank": 3},
         boss="cruiser", meteors=2.5),
    dict(name="Туманность Ориона", bg=(12, 2, 18), nebula=[(160, 40, 180), (70, 30, 150)],
         enemies={"soldier": 4, "splitter": 4, "sniper": 4, "kamikaze": 4},
         boss="guardian", meteors=0.8),
    dict(name="Родина пришельцев", bg=(2, 12, 6), nebula=[(30, 150, 70), (120, 140, 30)],
         enemies={"soldier": 3, "sniper": 3, "bomber": 3, "splitter": 3, "tank": 3, "kamikaze": 3},
         boss="emperor", meteors=1.2),
]

# ------------------------------------------------------------------ сложность
# hp/damage/fire/speed — множители для пришельцев, coins — для награды.
DIFFICULTIES = {
    "easy": dict(name="Лёгкий", hp=0.7, damage=0.6, fire=0.7, speed=0.85, coins=0.75,
                 color=(90, 220, 120)),
    "normal": dict(name="Нормальный", hp=1.0, damage=1.0, fire=1.0, speed=1.0, coins=1.0,
                   color=(120, 180, 255)),
    "hard": dict(name="Сложный", hp=1.4, damage=1.3, fire=1.3, speed=1.15, coins=1.6,
                 color=(255, 170, 60)),
    "nightmare": dict(name="Кошмар", hp=2.0, damage=1.7, fire=1.6, speed=1.3, coins=2.5,
                      color=(255, 70, 70)),
}
DIFFICULTY_ORDER = ["easy", "normal", "hard", "nightmare"]

# ------------------------------------------------------------------ пришельцы
#   hp      — базовое здоровье (растет с уровнем)
#   points  — очки, coins — монеты за уничтожение
#   shoot   — вероятность выстрела за кадр (боссы стреляют по своему расписанию)
#   ram     — урон кораблю игрока при таране
ALIEN_TYPES = {
    "scout": dict(name="Разведчик", image="alien_scout.png", size=(40, 30),
                  hp=1, points=10, coins=1, shoot=0.0, ram=30),
    "soldier": dict(name="Солдат", image="alien_soldier.png", size=(44, 34),
                    hp=3, points=25, coins=2, shoot=0.0022, ram=30),
    "kamikaze": dict(name="Камикадзе", image="alien_kamikaze.png", size=(36, 34),
                     hp=2, points=30, coins=3, shoot=0.0, ram=40),
    "tank": dict(name="Танк", image="alien_tank.png", size=(60, 40),
                 hp=8, points=60, coins=5, shoot=0.0012, ram=45),
    "bomber": dict(name="Бомбардировщик", image="alien_bomber.png", size=(64, 34),
                   hp=5, points=45, coins=4, shoot=0.0018, ram=40),
    "sniper": dict(name="Снайпер", image="alien_sniper.png", size=(34, 44),
                   hp=3, points=40, coins=4, shoot=0.0014, ram=30),
    "splitter": dict(name="Делитель", image="alien_splitter.png", size=(46, 32),
                     hp=4, points=35, coins=3, shoot=0.0, ram=35),
    "mini": dict(name="Осколок", image="alien_mini.png", size=(24, 20),
                 hp=1, points=5, coins=1, shoot=0.0, ram=20),
    # Боссы: hp умножается на номер уровня
    "mothership": dict(name="МАТКА", image="boss_mothership.png", size=(200, 110),
                       hp=40, points=1000, coins=60, shoot=0.0, ram=35, boss=True),
    "cruiser": dict(name="КРЕЙСЕР", image="boss_cruiser.png", size=(240, 90),
                    hp=42, points=1500, coins=80, shoot=0.0, ram=35, boss=True),
    "guardian": dict(name="СТРАЖ", image="boss_guardian.png", size=(160, 160),
                     hp=45, points=2000, coins=100, shoot=0.0, ram=35, boss=True),
    "emperor": dict(name="ИМПЕРАТОР", image="boss_emperor.png", size=(230, 140),
                    hp=50, points=3000, coins=150, shoot=0.0, ram=40, boss=True),
}

# Метеориты: (радиус, базовое здоровье, урон кораблю, очки, монеты)
METEORS = {
    1: dict(image="meteor_big.png", size=72, radius=30, hp=8, damage=40, points=20, coins=2),
    0: dict(image="meteor_small.png", size=38, radius=16, hp=3, damage=22, points=10, coins=1),
}

# Космический мусор: обломки кораблей. Если расстрелять, выпадает контейнер «?».
# Что внутри — выясняется, только когда игрок его подберет.
WRECKS = {
    0: dict(image="wreck_hull.png", size=(70, 50), hp=6, damage=15),
    1: dict(image="wreck_wing.png", size=(60, 46), hp=4, damage=12),
}
WRECKS_PER_10S = 0.8
# good — полезный ли эффект, weight — относительная частота,
# duration — длительность в кадрах (для временных эффектов)
PICKUPS = {
    "coins": dict(name="Монеты", good=True, weight=28),
    "repair": dict(name="Ремкомплект", good=True, weight=16),
    "shield": dict(name="Щит", good=True, weight=9, duration=300),
    "overdrive": dict(name="Форсаж оружия", good=True, weight=9, duration=600),
    "power": dict(name="Усилитель урона", good=True, weight=9, duration=600),
    "weapon": dict(name="Трофейное оружие", good=True, weight=8, duration=900),
    "life": dict(name="Запасной корабль", good=True, weight=3),
    "trap": dict(name="Ловушка!", good=False, weight=8),
    "virus": dict(name="Вирус: управление наоборот", good=False, weight=6, duration=360),
    "jam": dict(name="Помехи: оружие заклинило", good=False, weight=6, duration=240),
    "radiation": dict(name="Радиация", good=False, weight=6, duration=360),
    "corrosion": dict(name="Коррозия двигателей", good=False, weight=6, duration=360),
}

# ------------------------------------------------------------------ корабли игрока
# Базовые характеристики корпуса; улучшения из магазина добавляются сверху.
SHIPS = {
    "wanderer": dict(name="Странник", desc="Надежный корабль без слабых мест",
                     price=0, image="ship_2.bmp", size=(46, 59),
                     hp=100, speed=5.0, armor=0.0, guns=0, damage=1.0, firerate=1.0, lives=0),
    "interceptor": dict(name="Перехватчик", desc="Быстрый и скорострельный, но хрупкий",
                        price=600, image="ship_interceptor.png", size=(42, 58),
                        hp=80, speed=6.6, armor=0.0, guns=0, damage=0.95, firerate=1.3, lives=0),
    "assault": dict(name="Штурмовик", desc="Лишний ствол и легкая броня",
                    price=1400, image="ship_assault.png", size=(58, 58),
                    hp=120, speed=5.0, armor=0.05, guns=1, damage=1.0, firerate=1.0, lives=0),
    "fortress": dict(name="Крепость", desc="Медленная, но очень живучая",
                     price=2200, image="ship_fortress.png", size=(62, 64),
                     hp=200, speed=3.9, armor=0.15, guns=0, damage=1.1, firerate=0.9, lives=1),
    "phantom": dict(name="Фантом", desc="Мощные выстрелы и высокая скорость",
                    price=3500, image="ship_phantom.png", size=(52, 62),
                    hp=110, speed=6.0, armor=0.05, guns=1, damage=1.35, firerate=1.1, lives=0),
}
SHIP_ORDER = ["wanderer", "interceptor", "assault", "fortress", "phantom"]

# ------------------------------------------------------------------ оружие
# damage — урон одного снаряда, cooldown — кадров между залпами,
# pierce — сколько врагов снаряд пробивает насквозь, splash — радиус взрыва.
WEAPONS = {
    "blaster": dict(name="Бластер", desc="Надежное базовое оружие",
                    price=0, damage=1.0, cooldown=16, speed=10,
                    color=(127, 255, 212), size=(5, 14),
                    pierce=0, splash=0, homing=False),
    "laser": dict(name="Лазер", desc="Слабые, но очень частые выстрелы",
                  price=350, damage=0.55, cooldown=6, speed=18,
                  color=(255, 70, 70), size=(3, 24),
                  pierce=0, splash=0, homing=False),
    "plasma": dict(name="Плазма", desc="Мощные сгустки, пробивают 2 цели",
                   price=800, damage=3.2, cooldown=30, speed=8,
                   color=(190, 110, 255), size=(14, 14),
                   pierce=2, splash=0, homing=False),
    "rockets": dict(name="Ракеты", desc="Самонаведение и урон по площади",
                    price=1500, damage=2.6, cooldown=34, speed=6,
                    color=(255, 200, 80), size=(8, 16),
                    pierce=0, splash=60, homing=True),
}
WEAPON_ORDER = ["blaster", "laser", "plasma", "rockets"]

# Типы снарядов: меняют свойства выстрелов любого оружия (клавиша Q).
#   slow — на сколько кадров ледяной снаряд замедляет врага
AMMO = {
    "standard": dict(name="Обычные", desc="Без особых свойств", price=0,
                     damage=1.0, pierce=0, splash=0, slow=0, color=(255, 255, 255)),
    "piercing": dict(name="Бронебойные", desc="Пробивают еще одну цель, урон -10%", price=400,
                     damage=0.9, pierce=1, splash=0, slow=0, color=(230, 230, 255)),
    "explosive": dict(name="Разрывные", desc="Взрываются по площади, урон -20%", price=700,
                      damage=0.8, pierce=0, splash=40, slow=0, color=(255, 140, 40)),
    "cryo": dict(name="Ледяные", desc="Замедляют врагов на 2 секунды", price=900,
                 damage=0.9, pierce=0, splash=0, slow=120, color=(140, 220, 255)),
}
AMMO_ORDER = ["standard", "piercing", "explosive", "cryo"]

# ------------------------------------------------------------------ улучшения
# Цена уровня n: prices[n], либо base_price * growth ** n.
UPGRADES = {
    "damage": dict(name="Мощность оружия", max=10, base_price=60, growth=1.45),
    "firerate": dict(name="Скорострельность", max=8, base_price=70, growth=1.5),
    "guns": dict(name="Количество пушек", max=4, prices=[200, 500, 1100, 2200]),
    "armor": dict(name="Броня", max=8, base_price=80, growth=1.45),
    "hull": dict(name="Прочность корпуса", max=10, base_price=50, growth=1.4),
    "lives": dict(name="Запасные корабли", max=4, prices=[250, 600, 1200, 2500]),
    "engine": dict(name="Двигатели", max=6, base_price=60, growth=1.5),
    "regen": dict(name="Ремонтные дроны", max=5, base_price=150, growth=1.6),
}
UPGRADE_ORDER = ["damage", "firerate", "guns", "armor",
                 "hull", "lives", "engine", "regen"]


def upgrade_price(key, level):
    """Цена покупки следующего уровня улучшения (None — уровень максимальный)."""
    info = UPGRADES[key]
    if level >= info["max"]:
        return None
    if "prices" in info:
        return info["prices"][level]
    return int(round(info["base_price"] * info["growth"] ** level, -1))


def compute_stats(loadout):
    """Вычисляет характеристики корабля по корпусу, улучшениям, оружию и снарядам."""
    upgrades = loadout.get("upgrades", {})

    def lvl(key):
        return max(0, min(int(upgrades.get(key, 0)), UPGRADES[key]["max"]))

    def pick(value, table):
        return value if value in table else next(iter(table))

    weapon_id = pick(loadout.get("weapon"), WEAPONS)
    ship_id = pick(loadout.get("ship"), SHIPS)
    ammo_id = pick(loadout.get("ammo"), AMMO)
    weapon, ship, ammo = WEAPONS[weapon_id], SHIPS[ship_id], AMMO[ammo_id]
    stats = dict(
        weapon=weapon_id,
        ship=ship_id,
        ammo=ammo_id,
        max_hp=ship["hp"] + 25 * lvl("hull"),
        armor=min(0.8, ship["armor"] + 0.07 * lvl("armor")),
        lives=3 + ship["lives"] + lvl("lives"),
        guns=min(MAX_GUNS, 1 + ship["guns"] + lvl("guns")),
        damage_mult=ship["damage"] * (1 + 0.2 * lvl("damage")),
        cooldown=max(3, round(weapon["cooldown"] * 0.92 ** lvl("firerate") / ship["firerate"])),
        speed=ship["speed"] * (1 + 0.12 * lvl("engine")),
        regen=1.0 * lvl("regen"),
    )
    stats["dps"] = (stats["guns"] * weapon["damage"] * ammo["damage"] * stats["damage_mult"]
                    * FPS / stats["cooldown"])
    return stats


def world_of_level(level):
    """Номер мира (0..len(WORLDS)-1) для уровня; после последнего мира — снова первый."""
    return (level - 1) // LEVELS_PER_WORLD % len(WORLDS)
