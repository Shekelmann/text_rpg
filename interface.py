import os
import re
from enemy import Enemy_Rarity

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
    show_box([
        player.name,
        "Класс: —",
        f"HP: {player.health} / {player.max_health}",
        f"Мана: {player.mana} / {player.max_mana}",
        #f"Стамина: {player.stamina} / {player.max_stamina}",
        f"Золото: {player.gold}",
        f"Опыт: {player.exp}"
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

def show_inventory(inventory):
    print("\n=== Инвентарь ===")

    if not inventory.items:
        print("Инвентарь пуст.")
        return

    for i, item in enumerate(inventory.items, 1):
        print(f"{i}. {item.name}")
    print("0. Назад")

    choice = input("\nВыберите предмет: ")

    if choice == "0":
        return None

    if not choice.isdigit():
        print("Неверный выбор.")
        return None

    index = int(choice) - 1

    if 0 <= index < len(inventory.items):
        return inventory.items[index]

    print("Неверный выбор.")
    return None