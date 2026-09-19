import random
from copy import deepcopy
from affix_pool import WEAPON_AFFIX_POOL
from affix import AFFIX_COUNTS
from enemy import Enemy
from player import Player
from item import Inventory, Item, Armor
from world import World
from weapon import Weapon, Rarity
from damage import Damage_type
from loot import ENEMY_ITEM_DROP_CHANCE, LootTable, roll_item_rarity, roll_weapon_level

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

# Presentation metadata follows the existing canonical IDs through copies/loot.
for weapon_id, weapon_template in WEAPONS.items():
    weapon_template.icon_id = weapon_id

CLASS_STARTING_WEAPON_POOLS = {
    "bruiser": ("sword", "axe", "axe_2h", "club"),
    "daredevil": ("sword", "axe", "dagger"),
    "herald": ("staff", "staff_2h", "sword", "dagger"),
}

ARMOR = {
    "leather_armor": Armor("Кожаный доспех", 4, 12),
}


# Враги
ENEMIES = {
"goblin": {
"name": "Гоблин", 
"health": 160,
"min_damage": 7,
"max_damage": 11,
"crit_chance": 0.10, 
"dodge_chance": 0.04,
"damage_type": Damage_type.PHYSICAL,
"armor": 3,
"exp": 26,
"gold": (3, 7)
},

"wolf": {
"name": "Волк", 
"health": 145,
"min_damage": 6,
"max_damage": 10,
"crit_chance": 0.20, 
"dodge_chance": 0.12,
"damage_type": Damage_type.PHYSICAL,
"armor": 0,
"exp": 22,
},

"rat": {
"name": "Крыса",
"health": 105,
"min_damage": 4,
"max_damage": 7,
"crit_chance": 0.01,
"dodge_chance": 0.08,
"damage_type": Damage_type.PHYSICAL,
"armor": 0,
"exp": 12,
},

"likho": {
"name": "Лихо",
"health": 165,
"min_damage": 6,
"max_damage": 9,
"crit_chance": 0.12,
"dodge_chance": 0.06,
"damage_type": Damage_type.ASTRAL,
"armor": 0,
"exp": 30,
"gold": (5, 9)
},

"leshy": {
"name": "Леший",
"health": 185,
"min_damage": 8,
"max_damage": 12,
"crit_chance": 0.10,
"dodge_chance": 0,
"damage_type": Damage_type.PHYSICAL,
"armor": 4,
"exp": 34,
"gold": (6, 11)
},

"spider": {
"name": "Паук",
"health": 130,
"min_damage": 5,
"max_damage": 9,
"crit_chance": 0.20,
"dodge_chance": 0.15,
"damage_type": Damage_type.PHYSICAL,
"armor": 0,
"exp": 20,
},

"mutant": {
"name": "Выродок",
"health": 170,
"min_damage": 8,
"max_damage": 12,
"crit_chance": 0.10,
"dodge_chance": 0.02,
"damage_type": Damage_type.PHYSICAL,
"armor": 3,
"exp": 29,
"gold": (5, 9)
},

"skeleton": {
"name": "Скелет", 
"health": 170,
"min_damage": 7,
"max_damage": 11,
"crit_chance": 0.15, 
"dodge_chance": 0.03,
"damage_type": Damage_type.PHYSICAL,
"armor": 5,
"exp": 32,
"gold": (5, 9)
},

"draugr": {
"name": "Драугр",
"health": 190,
"min_damage": 9,
"max_damage": 13,
"crit_chance": 0.15,
"dodge_chance": 0,
"damage_type": Damage_type.PHYSICAL,
"armor": 6,
"exp": 40,
"gold": (7, 12)
},

"spirit": {
"name": "Дух",
"health": 165,
"min_damage": 7,
"max_damage": 10,
"crit_chance": 0.15,
"dodge_chance": 0.1,
"damage_type": Damage_type.ASTRAL,
"armor": 2,
"exp": 31,
"gold": (3, 6)
},

"undead": {
"name": "Мертвец",
"health": 185,
"min_damage": 8,
"max_damage": 12,
"crit_chance": 0.10,
"dodge_chance": 0,
"damage_type": Damage_type.PHYSICAL,
"armor": 4,
"exp": 35,
"gold": (4, 7)
},

"bandit": {
"name": "Бандит",
"health": 170,
"min_damage": 8,
"max_damage": 12,
"crit_chance": 0.20,
"dodge_chance": 0.1,
"damage_type": Damage_type.PHYSICAL,
"armor": 3,
"exp": 30,
"gold": (5, 9)
},

"orc": {
"name": "Орк",
"health": 195,
"min_damage": 10,
"max_damage": 14,
"crit_chance": 0.12,
"dodge_chance": 0.02,
"damage_type": Damage_type.PHYSICAL,
"armor": 6,
"exp": 44,
"gold": (8, 13)
},

"mountain_troll": {
"name": "Горный тролль",
"health": 230,
"min_damage": 12,
"max_damage": 16,
"crit_chance": 0.08,
"dodge_chance": 0,
"damage_type": Damage_type.PHYSICAL,
"armor": 8,
"exp": 58,
"gold": (10, 15)
},

"demon": {
"name": "Демон хаоса",
"health": 300,
"min_damage": 16,
"max_damage": 22,
"crit_chance": 0.2,
"dodge_chance": 0.04,
"damage_type": Damage_type.PHYSICAL,
"armor": 9,
"exp": 95,
"gold": (20, 35)
}
}


ITEMS = {
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
    "leather_armor": ARMOR["leather_armor"],
    #"gold": 
}

def create_item(item_id):
    template = ITEMS[item_id]

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
            icon_id=template.icon_id,
            level=template.level,
        )

    if isinstance(template, Armor):
        return deepcopy(template)

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
            item.level = roll_weapon_level(enemy_level, rng)
            item.generate_affixes(WEAPON_AFFIX_POOL, rng)
        return [item]
    return [create_item(item_id) for item_id in loot_table.roll(rng)]

def get_loot_table(enemy_id):
    table = ENEMY_LOOT.get(enemy_id)
    if table is None:
        return LootTable()
    return table.copy()

HUMANOID_LOOT = {
    "sword": 0.15,
    "axe": 0.10,
    "leather_armor": 0.40,
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
        "sword": 0.2,
        "leather_armor": 0.8
    })
})

# враги середины игры
#hellhound = "Адская гончая"
#brigand = "Бандит"
#zombie = "Мертвец"
#orc = "Орк"


def generate_starting_weapon(character_class, rng=None):
    """Generate one procedural weapon from the selected class pool."""
    rng = random if rng is None else rng
    class_id = getattr(character_class, "id", character_class)
    try:
        weapon_id = rng.choice(CLASS_STARTING_WEAPON_POOLS[class_id])
    except KeyError as error:
        raise ValueError(f"Unknown character class: {class_id}") from error
    weapon = deepcopy(WEAPONS[weapon_id])
    weapon.rarity = rng.choice(tuple(AFFIX_COUNTS))
    weapon.generate_affixes(WEAPON_AFFIX_POOL, rng)
    return weapon


def generate_starting_weapons(character_class, rng=None):
    """Generate independent procedural weapons from one class pool."""
    rng = random if rng is None else rng
    return [generate_starting_weapon(character_class, rng) for _ in range(3)]


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
    weapon.level = rng.randint(*level_range)
    weapon.rarity = rarity
    weapon.generate_affixes(WEAPON_AFFIX_POOL, rng)

    minimum_level, maximum_level = level_range
    gold = rng.randint(minimum_level * 5, maximum_level * 10)
    return {
        "weapon": weapon,
        "gold": gold,
    }
