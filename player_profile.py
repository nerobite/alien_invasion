import json
import os

from settings import UPGRADES, WEAPONS, SHIPS, AMMO, DIFFICULTIES, WORLDS, upgrade_price
from utils import data_path

# Разделы магазина с покупаемыми «один раз» предметами:
# таблица, поле «куплено», поле «выбрано»
ITEM_KINDS = {
    "weapon": (WEAPONS, "owned_weapons", "weapon"),
    "ship": (SHIPS, "owned_ships", "ship"),
    "ammo": (AMMO, "owned_ammo", "ammo"),
}


class Profile:
    """Сохраняемый прогресс игрока: монеты, рекорды, покупки и настройки."""

    def __init__(self, filename="save.json"):
        self.path = data_path(filename)
        self.coins = 0
        self.high_scores = {key: 0 for key in DIFFICULTIES}
        self.upgrades = {key: 0 for key in UPGRADES}
        for table, owned_attr, current_attr in ITEM_KINDS.values():
            setattr(self, owned_attr, [next(iter(table))])
            setattr(self, current_attr, next(iter(table)))
        self.unlocked_world = 0      # самый дальний открытый мир
        self.difficulty = "normal"   # последний выбор перед вылетом
        self.start_world = 0
        self.controls = "both"
        self.autofire = False
        self.load()

    def load(self):
        """Читает прогресс из файла, если он существует."""
        data = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                # Если файл битый — начинаем с нуля
                data = {}
        else:
            # Перенос рекорда из самой первой версии игры
            try:
                with open(data_path("high_score.json"), "r", encoding="utf-8") as f:
                    data = {"high_score": json.load(f).get("high_score", 0)}
            except (OSError, json.JSONDecodeError, AttributeError):
                pass

        self.coins = int(data.get("coins", 0))
        # Старый формат хранил один рекорд — считаем его рекордом «Нормального»
        self.high_scores["normal"] = int(data.get("high_score", 0))
        for key, score in data.get("high_scores", {}).items():
            if key in self.high_scores:
                self.high_scores[key] = int(score)
        for key, level in data.get("upgrades", {}).items():
            if key in UPGRADES:
                self.upgrades[key] = max(0, min(int(level), UPGRADES[key]["max"]))
        for table, owned_attr, current_attr in ITEM_KINDS.values():
            order = list(table)
            owned = {order[0]} | {i for i in data.get(owned_attr, []) if i in table}
            setattr(self, owned_attr, sorted(owned, key=order.index))
            current = data.get(current_attr)
            setattr(self, current_attr, current if current in owned else order[0])

        self.unlocked_world = max(0, min(int(data.get("unlocked_world", 0)), len(WORLDS) - 1))
        if data.get("difficulty") in DIFFICULTIES:
            self.difficulty = data["difficulty"]
        self.start_world = max(0, min(int(data.get("start_world", 0)), self.unlocked_world))
        self.controls = data.get("controls", "both")
        self.autofire = bool(data.get("autofire", False))

    def save(self):
        data = {
            "coins": self.coins,
            "high_scores": self.high_scores,
            "upgrades": self.upgrades,
            "unlocked_world": self.unlocked_world,
            "difficulty": self.difficulty,
            "start_world": self.start_world,
            "controls": self.controls,
            "autofire": self.autofire,
        }
        for _, owned_attr, current_attr in ITEM_KINDS.values():
            data[owned_attr] = getattr(self, owned_attr)
            data[current_attr] = getattr(self, current_attr)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    @property
    def best_score(self):
        return max(self.high_scores.values())

    def loadout(self):
        """Снаряжение корабля (передается в игровой мир и по сети)."""
        return {
            "upgrades": dict(self.upgrades),
            "ship": self.ship,
            "weapon": self.weapon,
            "ammo": self.ammo,
            "weapons": list(self.owned_weapons),
            "ammos": list(self.owned_ammo),
        }

    def unlock_world(self, world_index):
        if world_index > self.unlocked_world:
            self.unlocked_world = min(world_index, len(WORLDS) - 1)
            self.save()

    # ------------------------------------------------------------ покупки
    def next_upgrade_price(self, key):
        return upgrade_price(key, self.upgrades[key])

    def buy_upgrade(self, key):
        price = self.next_upgrade_price(key)
        if price is None or price > self.coins:
            return False
        self.coins -= price
        self.upgrades[key] += 1
        self.save()
        return True

    def owns(self, kind, item_id):
        return item_id in getattr(self, ITEM_KINDS[kind][1])

    def selected(self, kind):
        return getattr(self, ITEM_KINDS[kind][2])

    def buy_item(self, kind, item_id):
        """Покупает оружие, корабль или снаряды и сразу выбирает их."""
        table, owned_attr, current_attr = ITEM_KINDS[kind]
        price = table[item_id]["price"]
        if self.owns(kind, item_id) or price > self.coins:
            return False
        self.coins -= price
        getattr(self, owned_attr).append(item_id)
        getattr(self, owned_attr).sort(key=list(table).index)
        setattr(self, current_attr, item_id)
        self.save()
        return True

    def select_item(self, kind, item_id):
        if self.owns(kind, item_id):
            setattr(self, ITEM_KINDS[kind][2], item_id)
