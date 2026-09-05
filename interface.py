import os
import re
from enemy import Enemy_Rarity
from npc import TradeResult
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
    content_lines = [line for line in lines if line is not None]
    WIDTH = max(
        36,
        max((visible_length(line) for line in content_lines), default=0) + 4,
    )

    print("╔" + "═" * (WIDTH - 2) + "╗")

    for line in lines:
        if line is None:
            print("╠" + "═" * (WIDTH - 2) + "╣")
            continue
        padding = WIDTH - 4 - visible_length(line)
        print("║ " + line + " " * padding + " ║")

    print("╚" + "═" * (WIDTH - 2) + "╝")

BATTLE_ACTIONS = (
    "1 - Атака",
    "2 - Пропустить ход",
    "3 - Использовать зелье",
)

def show_battle_screen(player, enemy, messages=None, actions=None):
    messages = messages or ["Бой начинается."]
    actions = actions or BATTLE_ACTIONS
    sections = [
        [
            f"Противник: {enemy.name}",
            f"HP: {enemy.health} / {enemy.max_health}",
        ],
        [
            f"Игрок: {player.name}",
            f"HP: {player.health} / {player.max_health}",
            f"Мана: {player.mana} / {player.max_mana}",
        ],
        ["Действия:", *actions],
        ["Боевой лог:", *messages],
    ]
    content = [line for section in sections for line in section]
    width = max(60, max(visible_length(line) for line in content) + 4)

    clear()
    print("╔" + "═" * (width - 2) + "╗")
    title = " БОЙ "
    left_padding = (width - 2 - len(title)) // 2
    right_padding = width - 2 - len(title) - left_padding
    print("║" + " " * left_padding + title + " " * right_padding + "║")

    for section in sections:
        print("╠" + "═" * (width - 2) + "╣")
        for line in section:
            padding = width - 4 - visible_length(line)
            print("║ " + line + " " * padding + " ║")

    print("╚" + "═" * (width - 2) + "╝")

def show_player_status(player):
    if player.main_hand:
        bonus = player.get_direct_damage_bonus(player.main_hand.damage_type)
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
        f"Сила: {player.strength}",
        f"Ловкость: {player.dexterity}",
        f"Интеллект: {player.intelligence}",
        damage_text,
        f"Броня: {player.get_armor_defense()}",
        f"Золото: {player.gold}",
        None,
        f"HP: {player.health} / {player.max_health}",
        f"Мана: {player.mana} / {player.max_mana}",
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

STAT_CHOICES = (
    ("1", "strength", "Сила"),
    ("2", "dexterity", "Ловкость"),
    ("3", "intelligence", "Интеллект"),
)

def allocate_stat_points(player):
    while player.unspent_stat_points > 0:
        print("\nПовышение уровня! Распределите очко характеристики.")
        print(f"Очков: {player.unspent_stat_points}")
        print(f"Сила: {player.strength}  Ловкость: {player.dexterity}  Интеллект: {player.intelligence}")
        for key, _, label in STAT_CHOICES:
            print(f"{key}. {label}")

        choice = input("Выберите характеристику: ")
        selected = next((stat for key, stat, _ in STAT_CHOICES if key == choice), None)
        if selected and player.allocate_stat(selected):
            label = next(label for key, stat, label in STAT_CHOICES if stat == selected)
            print(f"{label} увеличена.")
        else:
            print("Неверный выбор.")

def choose_optional_enemy(enemy_names):
    while True:
        clear()
        show_box([
            "Оставшиеся враги:",
            *[
                f"{index}. {enemy_name}"
                for index, enemy_name in enumerate(enemy_names, 1)
            ],
            "0. Назад",
        ])
        choice = input("Выберите врага: ")
        if choice == "0":
            return None
        if choice.isdigit():
            enemy_index = int(choice) - 1
            if 0 <= enemy_index < len(enemy_names):
                return enemy_index
        print("Неверный выбор.")

TRADE_RESULT_MESSAGES = {
    TradeResult.NOT_AVAILABLE: "Этого предмета нет в ассортименте.",
    TradeResult.NOT_ENOUGH_GOLD: "Недостаточно золота.",
    TradeResult.INVENTORY_FULL: "В инвентаре нет свободного места.",
    TradeResult.ITEM_NOT_OWNED: "Этого предмета нет в инвентаре.",
}

def trade_with_merchant(player, merchant):
    message = None
    while True:
        clear()
        lines = [
            f"Торговец: {merchant.name}",
            f"Ваше золото: {player.gold}",
            None,
            "1. Купить",
            "2. Продать",
            "0. Назад",
        ]
        if message:
            lines.extend([None, message])
        show_box(lines)

        choice = input("Выберите действие: ")
        if choice == "0":
            return
        if choice == "1":
            while True:
                message = _buy_from_merchant(player, merchant, message)
                if message is None:
                    break
        elif choice == "2":
            while True:
                message = _sell_to_merchant(player, merchant, message)
                if message is None:
                    break
        else:
            message = "Неверный выбор."

def _buy_from_merchant(player, merchant, message=None):
    offers = list(merchant.assortment.items())
    clear()
    lines = [
        f"Покупка у {merchant.name}",
        f"Ваше золото: {player.gold}",
        None,
        *[
            f"{index}. {format_item_for_menu(merchant.get_offer_item(item_id))} — {price} золота"
            for index, (item_id, price) in enumerate(offers, 1)
        ],
        "0. Назад",
    ]
    if message:
        lines.extend([None, message])
    show_box(lines)
    choice = input("Выберите предмет: ")
    if choice == "0":
        return None
    if not choice.isdigit() or not 0 < int(choice) <= len(offers):
        return "Неверный выбор."

    item_id, price = offers[int(choice) - 1]
    item_name = merchant.get_offer_name(item_id)
    confirmation = input(
        f"\u041a\u0443\u043f\u0438\u0442\u044c {item_name} \u0437\u0430 {price} \u0437\u043e\u043b\u043e\u0442\u0430? (1 \u2014 \u0434\u0430, 0 \u2014 \u043d\u0435\u0442): "
    )
    if confirmation != "1":
        return "\u041f\u043e\u043a\u0443\u043f\u043a\u0430 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430."
    result = merchant.buy_item(player, item_id)
    if result == TradeResult.SUCCESS:
        return f"Куплено: {item_name}."
    return TRADE_RESULT_MESSAGES[result]

def _sell_to_merchant(player, merchant, message=None):
    items = list(player.inventory.items)
    if not items:
        clear()
        lines = [
            f"\u041f\u0440\u043e\u0434\u0430\u0436\u0430: {merchant.name}",
            f"\u0412\u0430\u0448\u0435 \u0437\u043e\u043b\u043e\u0442\u043e: {player.gold}",
            None,
            "\u0412 \u0438\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u0435 \u043d\u0435\u0442 \u043f\u0440\u0435\u0434\u043c\u0435\u0442\u043e\u0432 \u0434\u043b\u044f \u043f\u0440\u043e\u0434\u0430\u0436\u0438.",
            "0. \u041d\u0430\u0437\u0430\u0434",
        ]
        if message:
            lines.extend([None, message])
        show_box(lines)
        choice = input("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435: ")
        if choice == "0":
            return None
        return "В инвентаре нет предметов для продажи."

    clear()
    lines = [
        f"Продажа: {merchant.name}",
        f"Ваше золото: {player.gold}",
        None,
        *[
            f"{index}. {format_item_for_menu(item)} — {merchant.get_sell_price(item)} золота"
            for index, item in enumerate(items, 1)
        ],
        "0. Назад",
    ]
    if message:
        lines.extend([None, message])
    show_box(lines)
    choice = input("Выберите предмет: ")
    if choice == "0":
        return None
    if not choice.isdigit() or not 0 < int(choice) <= len(items):
        return "Неверный выбор."

    item = items[int(choice) - 1]
    price = merchant.get_sell_price(item)
    confirmation = input(
        f"\u041f\u0440\u043e\u0434\u0430\u0442\u044c {item.name} \u0437\u0430 {price} \u0437\u043e\u043b\u043e\u0442\u0430? (1 \u2014 \u0434\u0430, 0 \u2014 \u043d\u0435\u0442): "
    )
    if confirmation != "1":
        return "\u041f\u0440\u043e\u0434\u0430\u0436\u0430 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430."
    result = merchant.sell_item(player, item)
    if result == TradeResult.SUCCESS:
        return f"Продано: {item.name} за {price} золота."
    return TRADE_RESULT_MESSAGES[result]

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


ITEM_MENU_SUMMARY_FORMATTERS = {
    "weapon": lambda item: f"урон: {item.min_damage}–{item.max_damage}",
    "potion": lambda item: f"восполняет {item.heal} здоровья",
}


def format_item_for_menu(item):
    formatter = ITEM_MENU_SUMMARY_FORMATTERS.get(get_item_category(item))
    if formatter is None:
        return item.name
    return f"{item.name} ({formatter(item)})"

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
            print(f"{i}. {format_item_for_menu(item)}{equipped_mark}")
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
            if source == "inventory":
                if player.equip_weapon(item):
                    print(f"\n\u042d\u043a\u0438\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u043e: {item.name}.")
                else:
                    print("\n\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u044d\u043a\u0438\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043e\u0440\u0443\u0436\u0438\u0435.")
                continue
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
            if source == "inventory":
                if player.equip_armor(item):
                    print(f"\n\u042d\u043a\u0438\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u043e: {item.name}.")
                else:
                    print("\n\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u044d\u043a\u0438\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0431\u0440\u043e\u043d\u044e.")
                continue
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
