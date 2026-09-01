import os
import re
from enemy import Enemy_Rarity
from player import ARMOR_SLOTS

#def show_player_status(player):
    #WIDTH = 36

    #def box_line(text):
        #print("║ " + text.ljust(WIDTH - 4) + " ║")

    #print("╔" + "═" * (WIDTH - 2) + "╗")

    #box_line(f"{player.name:<26}")
    #box_line(f"Класс: {'—':<20}")
    #box_line(f"HP:      {player.health:<3} / {player.max_health:<3}")
    #box_line(f"Мана:    {player.mana:<3} / {player.max_mana:<3}")
    #box_line(f"Стамина: {player.stamina:<3} / {player.max_stamina:<3}")
    #box_line(f"Золото:  {player.gold:<18}")
    #box_line(f"Опыт:    {player.exp:<18}")

    #print("╚" + "═" * (WIDTH - 2) + "╝")

#Добавляет 1 экран и убирает скроллинг
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
def show_game_screen(player, location, enemy=None): 
    clear()

    print("╔══════════════════════════════════════╗")
    print(f"║ Уровень: {player.level:<5} HP: {player.health}/{player.max_health:<8} ║")
    print(f"║ Сила: {player.strength:<3} Ловкость: {player.dexterity:<3} Интеллект: {player.intelligence:<3} ║")
    print("╠══════════════════════════════════════╣")
    print(f"║ Локация: {location}")
    print("║")

    if enemy:
        print(f"║ Враг: {enemy.name}")
        print(f"║ HP: {enemy.health}/{enemy.max_health}")
    print("╚══════════════════════════════════════╝")

ANSI_PATTERN = re.compile(r'\033\[[0-9;]*m')

def visible_length(text):
    return len(ANSI_PATTERN.sub('', text))

def show_box(lines):
    WIDTH = 36

    print("╔" + "═" * (WIDTH - 2) + "╗")

    for line in lines:
        padding = WIDTH - 4 - visible_length(line)
        print("║ " + line + " " * padding + " ║")

    print("╚" + "═" * (WIDTH - 2) + "╝")

def show_player_status(player):
    if player.main_hand:
        bonus = player.get_physical_damage_bonus()
        damage_text = (
            f"Урон: {player.main_hand.min_damage + bonus}–"
            f"{player.main_hand.max_damage + bonus}"
        )
    else:
        damage_text = "Урон: —"

    class_name = player.character_class.name if player.character_class else "—"

    show_box([
        f"Имя: {player.name}",
        f"Класс: {class_name}",
        f"HP: {player.health} / {player.max_health}",
        f"Мана: {player.mana} / {player.max_mana}",
        #f"Стамина: {player.stamina} / {player.max_stamina}",
        f"Сила: {player.strength}",
        f"Ловкость: {player.dexterity}",
        f"Интеллект: {player.intelligence}",
        damage_text,
        f"Броня: {player.get_armor_defense()}",
        f"Золото: {player.gold}",
        f"Уровень: {player.level}",
        f"Опыт: {player.exp}/{player.exp_to_level}"
    ])

def show_enemy_status(enemy):
    color = get_rarity_color(enemy.rarity)

    show_box([
        f"{color}{enemy.name}{RESET}",
        f"HP: {enemy.health} / {enemy.max_health}"
    ])

def get_rarity_color(rarity):
    colors = {
        "common": "\033[32m",
        "dangerous": "\033[34m",
        "elite": "\033[31m"
    }

    return colors.get(rarity, "\033[0m")

RESET = "\033[0m"

def choose_character_class():
    from character_class import CLASS_LIST

    while True:
        print("\nВыберите класс:\n")
        for i, character_class in enumerate(CLASS_LIST, 1):
            print(f"{i}. {character_class.name}")
            print(character_class.description)
            print(f"HP: {character_class.max_health}")
            print(f"Сила: {character_class.strength}")
            print(f"Ловкость: {character_class.dexterity}")
            print(f"Интеллект: {character_class.intelligence}")
            print()

        choice = input("Выберите класс (номер): ")
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(CLASS_LIST):
                return CLASS_LIST[index]
        print("Неверный выбор.")

INVENTORY_CATEGORIES = [
    ("potion", "Зелья"),
    ("scroll", "Свитки"),
    ("consumable", "Расходники"),
    ("weapon", "Оружие"),
    ("armor", "Броня"),
    ("accessory", "Аксессуары"),
    ("other", "Остальное"),
]

def get_item_category(item):
    item_type = getattr(item, "item_type", None)

    if getattr(item, "is_weapon", False) or item_type == "weapon":
        return "weapon"
    if item_type == "potion":
        return "potion"
    if item_type == "scroll":
        return "scroll"
    if item_type == "consumable":
        return "consumable"
    if item_type == "armor":
        return "armor"
    if item_type == "accessory":
        return "accessory"
    return "other"

def _equipped_weapons(player):
    weapons = []
    if player.main_hand is not None:
        weapons.append(player.main_hand)
    if player.off_hand is not None and player.off_hand is not player.main_hand:
        weapons.append(player.off_hand)
    return weapons

def _equipped_armor(player):
    pieces = []
    for slot in ARMOR_SLOTS:
        armor = getattr(player, slot, None)
        if armor is not None:
            pieces.append(armor)
    return pieces

def _category_entries(player, category_id):
    inventory_items = [
        item for item in player.inventory.items
        if get_item_category(item) == category_id
    ]

    if category_id == "weapon":
        equipped_items = _equipped_weapons(player)
    elif category_id == "armor":
        equipped_items = _equipped_armor(player)
    else:
        return [("inventory", item) for item in inventory_items]

    entries = []
    seen = set()
    for item in equipped_items:
        entries.append(("equipped", item))
        seen.add(id(item))
    for item in inventory_items:
        if id(item) not in seen:
            entries.append(("inventory", item))
    return entries

def _damage_type_text(weapon):
    damage_type = getattr(weapon, "damage_type", None)
    if hasattr(damage_type, "value"):
        return damage_type.value
    return str(damage_type)

def _show_weapon_details(weapon, equipped):
    print(f"\nНазвание: {weapon.name}")
    print(f"Урон: {weapon.min_damage}–{weapon.max_damage}")
    print(f"Шанс критического удара: {weapon.crit_chance:.0%}")
    print(f"Тип: {weapon.weapon_type}")
    print(f"Тип урона: {_damage_type_text(weapon)}")
    if equipped:
        print("Экипировано")

    if equipped:
        print("\n1. Снять")
    else:
        print("\n1. Экипировать")
    print("0. Назад")

    choice = input("\nВыберите действие: ")
    if choice == "1":
        return "unequip" if equipped else "equip"
    return None

def _show_armor_details(armor, equipped):
    print(f"\nНазвание: {armor.name}")
    print(f"Защита: {armor.defense}")
    if equipped:
        print("Экипировано")

    if equipped:
        print("\n1. Снять")
    else:
        print("\n1. Экипировать")
    print("0. Назад")

    choice = input("\nВыберите действие: ")
    if choice == "1":
        return "unequip" if equipped else "equip"
    return None

def _show_category(player, category_id, category_name):
    while True:
        entries = _category_entries(player, category_id)
        print(f"\n=== {category_name} ===")

        if not entries:
            print("В этой категории нет предметов.")
            print("0. Назад")
            choice = input("\nВыберите действие: ")
            return None

        for i, (source, item) in enumerate(entries, 1):
            equipped_mark = " [Экипировано]" if source == "equipped" else ""
            print(f"{i}. {item.name}{equipped_mark}")
        print("0. Назад")

        choice = input("\nВыберите предмет: ")
        if choice == "0":
            return None

        if not choice.isdigit():
            print("Неверный выбор.")
            continue

        index = int(choice) - 1
        if not (0 <= index < len(entries)):
            print("Неверный выбор.")
            continue

        source, item = entries[index]

        if getattr(item, "is_weapon", False):
            action = _show_weapon_details(item, equipped=(source == "equipped"))
            if action == "equip":
                return item
            if action == "unequip":
                if player.unequip_weapon():
                    print("\nВы сняли оружие.")
                else:
                    print("\nНе удалось снять оружие.")
            continue

        if get_item_category(item) == "armor":
            action = _show_armor_details(item, equipped=(source == "equipped"))
            if action == "equip":
                return item
            if action == "unequip":
                if player.unequip_armor(item.slot):
                    print("\nВы сняли броню.")
                else:
                    print("\nНе удалось снять броню.")
            continue

        return item

def show_inventory(player):
    while True:
        print("\n=== Инвентарь ===")
        print(f"Занято: {len(player.inventory.items)}/{player.inventory.size}")
        for i, (_, name) in enumerate(INVENTORY_CATEGORIES, 1):
            print(f"{i}. {name}")
        print("0. Назад")

        choice = input("\nВыберите категорию: ")
        if choice == "0":
            return None

        if not choice.isdigit():
            print("Неверный выбор.")
            continue

        index = int(choice) - 1
        if not (0 <= index < len(INVENTORY_CATEGORIES)):
            print("Неверный выбор.")
            continue

        category_id, category_name = INVENTORY_CATEGORIES[index]
        item = _show_category(player, category_id, category_name)
        if item is not None:
            return item