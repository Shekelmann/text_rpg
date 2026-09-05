import random
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
"sword": Weapon("Меч", 3, 7, 0.15, "Одноручное", Damage_type.PHYSICAL, 12),
"sword_2h": Weapon("Двуручный меч", 8, 15, 0.20, "Двуручное", Damage_type.PHYSICAL, 25),
"axe": Weapon("Топор", 4, 9, 0.10, "Одноручное", Damage_type.PHYSICAL, 15),
"axe_2h": Weapon("Двуручный топор", 10, 19, 0.18, "Двуручное", Damage_type.PHYSICAL, 30),
"dagger": Weapon("Кинжал", 1, 5, 0.30, "Одноручное", Damage_type.PHYSICAL, 10),
"spear": Weapon("Копье", 5, 8, 0.20, "Двуручное", Damage_type.PHYSICAL, 18),
"club": Weapon("Дубина", 10, 12, 0.09, "Одноручное", Damage_type.PHYSICAL, 14),
"club_2h": Weapon("Двуручная дубина", 17, 19, 0.11, "Двуручное", Damage_type.PHYSICAL, 28)
}

# магическое оружие

#light_totem = Weapon("Тотем молнии", 10, 17, 0.05, "Одноручное", Damage_type.LIGHTNING, 1,5) # Подумать, как прикрутить ману

# легендарное оружие  

STARTER_WEAPON = Weapon(
    "Простой меч",
    2,
    5,
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
"health": 15, 
"min_damage": 2, 
"max_damage": 4, 
"crit_chance": 0.10, 
"damage_type": Damage_type.PHYSICAL,
"gold": (1, 3)
},

"wolf": {
"name": "Волк", 
"health": 10, 
"min_damage": 2, 
"max_damage": 3, 
"crit_chance": 0.20, 
"damage_type": Damage_type.PHYSICAL
},

"rat": {
"name": "Крыса", 
"health": 5, 
"min_damage": 1, 
"max_damage": 3, 
"crit_chance": 0.01, 
"damage_type": Damage_type.PHYSICAL
},

"spider": {
"name": "Паук", 
"health": 7, 
"min_damage": 2, 
"max_damage": 5, 
"crit_chance": 0.20, 
"damage_type": Damage_type.PHYSICAL
},

"skeleton": {
"name": "Скелет", 
"health": 20, 
"min_damage": 3, 
"max_damage": 5, 
"crit_chance": 0.15, 
"damage_type": Damage_type.PHYSICAL,
"gold": (2, 4)
},

"demon": {
"name": "Демон хаоса",
"health": 40,
"min_damage": 7,
"max_damage": 12,
"crit_chance": 0.2,
"damage_type": Damage_type.PHYSICAL,
"gold": (20, 35)
}
}


ITEMS = {
    "heal": Heal(10, 6),
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
