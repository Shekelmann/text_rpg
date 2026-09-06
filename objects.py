import random
from copy import deepcopy
from affix_pool import WEAPON_AFFIX_POOL
from affix import AFFIX_COUNTS
from enemy import Enemy
from player import Player
from item import Inventory, Item, Heal, Armor 
from world import World
from weapon import Weapon, Rarity
from damage import Damage_type
from loot import LootTable

# Оружие
# базовое оружие
WEAPONS = {
"sword": Weapon("Меч", 12, 28, 0.15, "Одноручное", Damage_type.PHYSICAL, 12),
"sword_2h": Weapon("Двуручный меч", 32, 60, 0.20, "Двуручное", Damage_type.PHYSICAL, 25),
"axe": Weapon("Топор", 16, 36, 0.10, "Одноручное", Damage_type.PHYSICAL, 15),
"axe_2h": Weapon("Двуручный топор", 40, 76, 0.18, "Двуручное", Damage_type.PHYSICAL, 30),
"dagger": Weapon("Кинжал", 4, 20, 0.30, "Одноручное", Damage_type.PHYSICAL, 10),
"spear": Weapon("Копье", 20, 32, 0.20, "Двуручное", Damage_type.PHYSICAL, 18),
"club": Weapon("Дубина", 40, 48, 0.09, "Одноручное", Damage_type.PHYSICAL, 14),
"club_2h": Weapon("Двуручная дубина", 68, 76, 0.11, "Двуручное", Damage_type.PHYSICAL, 28)
}

# магическое оружие

#light_totem = Weapon("Тотем молнии", 10, 17, 0.05, "Одноручное", Damage_type.LIGHTNING, 1,5) # Подумать, как прикрутить ману

# легендарное оружие  

STARTER_WEAPON = Weapon(
    "Простой меч",
    10,
    18,
    0.10,
    "Одноручное",
    Damage_type.PHYSICAL,
    3,
)

ARMOR = {
    "leather_helmet": Armor("Кожаный шлем", "head", 1, 5),
    "leather_chest": Armor("Кожаный доспех", "body", 2, 12),
    "leather_gloves": Armor("Кожаные перчатки", "hands", 1, 6),
    "leather_boots": Armor("Кожаные сапоги", "legs", 1, 6),
}


# Враги
ENEMIES = {
"goblin": {
"name": "Гоблин", 
"health": 100,
"min_damage": 8,
"max_damage": 16,
"crit_chance": 0.10, 
"damage_type": Damage_type.PHYSICAL,
"gold": (1, 3)
},

"wolf": {
"name": "Волк", 
"health": 90,
"min_damage": 8,
"max_damage": 12,
"crit_chance": 0.20, 
"damage_type": Damage_type.PHYSICAL
},

"rat": {
"name": "Крыса", 
"health": 70,
"min_damage": 8,
"max_damage": 10,
"crit_chance": 0.01, 
"damage_type": Damage_type.PHYSICAL
},

"spider": {
"name": "Паук", 
"health": 80,
"min_damage": 10,
"max_damage": 16,
"crit_chance": 0.20, 
"damage_type": Damage_type.PHYSICAL
},

"skeleton": {
"name": "Скелет", 
"health": 120,
"min_damage": 12,
"max_damage": 18,
"crit_chance": 0.15, 
"damage_type": Damage_type.PHYSICAL,
"gold": (2, 4)
},

"demon": {
"name": "Демон хаоса",
"health": 180,
"min_damage": 28,
"max_damage": 48,
"crit_chance": 0.2,
"damage_type": Damage_type.PHYSICAL,
"gold": (20, 35)
}
}


ITEMS = {
    "heal": Heal(40, 6),
    "sword": WEAPONS["sword"],
    "2 handed sword": WEAPONS["sword_2h"],
    "axe": WEAPONS["axe"],
    "2 handed axe": WEAPONS["axe_2h"],
    "dagger": WEAPONS["dagger"],
    "leather_helmet": ARMOR["leather_helmet"],
    "leather_chest": ARMOR["leather_chest"],
    "leather_gloves": ARMOR["leather_gloves"],
    "leather_boots": ARMOR["leather_boots"],
    #"gold": 
}

def create_item(item_id):
    template = ITEMS[item_id]

    if isinstance(template, Heal):
        return Heal(template.heal, template.price)

    if isinstance(template, Weapon):
        return Weapon(
            template.name,
            template.min_damage,
            template.max_damage,
            template.crit_chance,
            template.weapon_type,
            template.damage_type,
            template.price,
            rarity=template.rarity,
            affixes=template.affixes,
        )

    if isinstance(template, Armor):
        return Armor(
            template.name,
            template.slot,
            template.defense,
            template.price,
        )

    raise TypeError(f"Неизвестный тип предмета: {item_id}")

def generate_loot(loot_table, rng=None):
    if loot_table is None:
        return []
    return [create_item(item_id) for item_id in loot_table.roll(rng)]

def get_loot_table(enemy_id):
    table = ENEMY_LOOT.get(enemy_id)
    if table is None:
        return LootTable()
    return table.copy()

ENEMY_LOOT = {
    "goblin": LootTable.from_mapping({
        "heal": 0.5,
        "sword": 0.2,
        "leather_helmet": 0.2,
        "leather_chest": 0.2,
        "leather_gloves": 0.2,
        "leather_boots": 0.2
    }),
    "skeleton": LootTable.from_mapping({
        "heal": 0.5,
        "axe": 0.2,
        "leather_helmet": 0.2,
        "leather_chest": 0.2,
        "leather_gloves": 0.2,
        "leather_boots": 0.2
    }),
    "demon": LootTable.from_mapping({
        "heal": 1,
        "sword": 0.2,
        "leather_helmet": 0.2,
        "leather_chest": 0.2,
        "leather_gloves": 0.2,
        "leather_boots": 0.2
    })
}

# враги середины игры
#hellhound = "Адская гончая"
#brigand = "Бандит"
#zombie = "Мертвец"
#orc = "Орк"


# Новая таблица для врага:
# ENEMY_LOOT["wolf"] = LootTable.from_mapping({
#     "heal": 0.3,
# })


def generate_starting_weapons(rng=None):
    """Three independent test weapons; ordinary loot/shop creation stays unchanged."""
    rng = random if rng is None else rng
    weapons = []
    for _ in range(3):
        weapon = deepcopy(rng.choice(tuple(WEAPONS.values())))
        weapon.rarity = rng.choice(tuple(AFFIX_COUNTS))
        weapon.generate_affixes(WEAPON_AFFIX_POOL, rng)
        weapons.append(weapon)
    return weapons
