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
from loot import ENEMY_ITEM_DROP_CHANCE, LootTable, roll_item_rarity

CHEST_RARITY_WEIGHTS = (
    (1, 3, {Rarity.RARE: 0.80, Rarity.EPIC: 0.20}),
    (4, 7, {Rarity.RARE: 0.65, Rarity.EPIC: 0.35}),
    (8, 12, {Rarity.RARE: 0.50, Rarity.EPIC: 0.50}),
)

# Оружие
# базовое оружие
WEAPONS = {
"sword": Weapon("Меч", 12, 28, 0.15, "Одноручное", Damage_type.PHYSICAL, 12),
"axe": Weapon("Топор", 16, 36, 0.10, "Одноручное", Damage_type.PHYSICAL, 15),
"axe_2h": Weapon("Двуручный топор", 40, 76, 0.18, "Двуручное", Damage_type.PHYSICAL, 30),
"dagger": Weapon("Кинжал", 4, 20, 0.30, "Одноручное", Damage_type.PHYSICAL, 10),
"club": Weapon("Палица", 40, 48, 0.09, "Одноручное", Damage_type.PHYSICAL, 14),
"staff": Weapon("Одноручный посох", 10, 24, 0.10, "Одноручное", Damage_type.ASTRAL, 15),
"staff_2h": Weapon("Двуручный посох", 28, 52, 0.12, "Двуручное", Damage_type.ASTRAL, 28),
}

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

"likho": {
"name": "Лихо",
"health": 110,
"min_damage": 10,
"max_damage": 17,
"crit_chance": 0.12,
"damage_type": Damage_type.ASTRAL,
"gold": (2, 4)
},

"leshy": {
"name": "Леший",
"health": 130,
"min_damage": 12,
"max_damage": 19,
"crit_chance": 0.10,
"damage_type": Damage_type.PHYSICAL,
"gold": (3, 5)
},

"spider": {
"name": "Паук",
"health": 80,
"min_damage": 10,
"max_damage": 16,
"crit_chance": 0.20,
"damage_type": Damage_type.PHYSICAL
},

"mutant": {
"name": "Выродок",
"health": 100,
"min_damage": 11,
"max_damage": 17,
"crit_chance": 0.10,
"damage_type": Damage_type.PHYSICAL,
"gold": (2, 4)
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

"draugr": {
"name": "Драугр",
"health": 140,
"min_damage": 14,
"max_damage": 21,
"crit_chance": 0.15,
"damage_type": Damage_type.PHYSICAL,
"gold": (4, 7)
},

"spirit": {
"name": "Дух",
"health": 115,
"min_damage": 12,
"max_damage": 18,
"crit_chance": 0.15,
"damage_type": Damage_type.ASTRAL,
"gold": (2, 5)
},

"undead": {
"name": "Мертвец",
"health": 130,
"min_damage": 13,
"max_damage": 20,
"crit_chance": 0.10,
"damage_type": Damage_type.PHYSICAL,
"gold": (3, 6)
},

"bandit": {
"name": "Бандит",
"health": 120,
"min_damage": 13,
"max_damage": 21,
"crit_chance": 0.20,
"damage_type": Damage_type.PHYSICAL,
"gold": (5, 9)
},

"orc": {
"name": "Орк",
"health": 140,
"min_damage": 15,
"max_damage": 23,
"crit_chance": 0.12,
"damage_type": Damage_type.PHYSICAL,
"gold": (6, 10)
},

"mountain_troll": {
"name": "Горный тролль",
"health": 180,
"min_damage": 18,
"max_damage": 28,
"crit_chance": 0.08,
"damage_type": Damage_type.PHYSICAL,
"gold": (8, 14)
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
    "spider_gland": Item(
        "Паучья железа",
        "material",
        use_in_combat=False,
        price=10,
        sell_price=5,
    ),
    "wolf_pelt": Item(
        "Волчья шкура",
        "material",
        use_in_combat=False,
        price=16,
        sell_price=8,
    ),
    "sword": WEAPONS["sword"],
    "axe": WEAPONS["axe"],
    "2 handed axe": WEAPONS["axe_2h"],
    "dagger": WEAPONS["dagger"],
    "staff": WEAPONS["staff"],
    "2 handed staff": WEAPONS["staff_2h"],
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

    if isinstance(template, Item):
        return Item(
            template.name,
            template.item_type,
            template.use_in_combat,
            template.price,
            rarity=template.rarity,
            sell_price=template.sell_price,
        )

    raise TypeError(f"Неизвестный тип предмета: {item_id}")

def generate_loot(loot_table, rng=None, enemy_level=None):
    if loot_table is None:
        return []
    if enemy_level is not None:
        rng = random if rng is None else rng
        if not loot_table.entries or rng.random() >= ENEMY_ITEM_DROP_CHANCE:
            return []
        entry = rng.choices(
            loot_table.entries,
            weights=[entry.chance for entry in loot_table.entries],
        )[0]
        item = create_item(entry.item_id)
        item.rarity = roll_item_rarity(enemy_level, rng)
        if isinstance(item, Weapon):
            item.generate_affixes(WEAPON_AFFIX_POOL, rng)
        return [item]
    return [create_item(item_id) for item_id in loot_table.roll(rng)]

def get_loot_table(enemy_id):
    table = ENEMY_LOOT.get(enemy_id)
    if table is None:
        return LootTable()
    return table.copy()

HUMANOID_LOOT = {
    "heal": 0.25,
    "sword": 0.15,
    "axe": 0.10,
    "leather_helmet": 0.10,
    "leather_chest": 0.10,
    "leather_gloves": 0.10,
    "leather_boots": 0.10,
}

HUMANOID_ENEMIES = (
    "goblin",
    "mutant",
    "skeleton",
    "draugr",
    "undead",
    "orc",
    "bandit",
    "mountain_troll",
)

ENEMY_LOOT = {
    enemy_id: LootTable.from_mapping(HUMANOID_LOOT)
    for enemy_id in HUMANOID_ENEMIES
}
ENEMY_LOOT.update({
    "spider": LootTable.from_mapping({"spider_gland": 0.50}),
    "wolf": LootTable.from_mapping({"wolf_pelt": 0.50}),
    "demon": LootTable.from_mapping({
        "heal": 1,
        "sword": 0.2,
        "leather_helmet": 0.2,
        "leather_chest": 0.2,
        "leather_gloves": 0.2,
        "leather_boots": 0.2
    })
})

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


def get_chest_rarity_chances(level_range):
    zone_level = level_range[1]
    for minimum, maximum, chances in CHEST_RARITY_WEIGHTS:
        if minimum <= zone_level <= maximum:
            return chances
    if zone_level < CHEST_RARITY_WEIGHTS[0][0]:
        return CHEST_RARITY_WEIGHTS[0][2]
    return CHEST_RARITY_WEIGHTS[-1][2]


def generate_chest_reward(level_range, rng=None):
    rng = random if rng is None else rng
    rarity_chances = get_chest_rarity_chances(level_range)
    rarity = rng.choices(
        list(rarity_chances.keys()),
        weights=rarity_chances.values(),
    )[0]
    weapon = deepcopy(rng.choice(tuple(WEAPONS.values())))
    weapon.rarity = rarity
    weapon.generate_affixes(WEAPON_AFFIX_POOL, rng)

    minimum_level, maximum_level = level_range
    gold = rng.randint(minimum_level * 5, maximum_level * 10)
    return {
        "weapon": weapon,
        "gold": gold,
    }
