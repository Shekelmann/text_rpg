from game_io import input, print, present, bind_state
from enemy import Enemy
from player import Player
from item import Inventory, Item 
from world import World
from weapon import Weapon, Rarity
from objects import WEAPONS, ENEMIES, generate_starting_weapons
from battle import player_turn, enemy_turn, battle
#from enemy_generator import generate_enemy
from interface import show_player_status, choose_character_class
from encounter import claim_location_chest, handle_encounter, hunt_optional_enemies
from interface import (
    clear,
    configure_loot_filter,
    get_item_category,
    show_ground_loot,
    show_inventory,
    trade_with_merchant,
)
from damage import Damage_type
from npc import Merchant
from npcs import get_npc

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это пре-альфа версия ролевой игры в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    
    name = input("Введите имя героя: ", kind="text", default="Герой") # Вводим имя
    character_class = choose_character_class()
    starting_weapons = generate_starting_weapons(character_class)
    player = Player(name, starting_weapons[0], character_class) # Создаем игрока
    for weapon in starting_weapons[1:]:
        player.inventory.add_item(weapon)

    # Создаем мир
    world = World()
    player.current_location = "village"
    bind_state(player, world)
    paths = world.show_paths(player.current_location)

    # Игровой цикл
    while True:
        clear()
        show_player_status(player)

        locations = world.locations.get(player.current_location)

        menu_options = get_location_menu_options(world, player.current_location)
        if not present("location", player=player, world=world, options=menu_options):
            print("\n=====================")
            print(f"Текущая локация: {locations['name']}")
            for index, (_, label) in enumerate(menu_options, 1):
                print(f"\n{index}. {label}")
        
        choice = input("\nВыберите действие: ", kind="location")
        if choice.startswith("flask:"):
            player.use_flask(choice.split(":", 1)[1])
            continue
        if not choice.isdigit():
            continue
        choice_index = int(choice) - 1
        if not 0 <= choice_index < len(menu_options):
            continue
        action = menu_options[choice_index][0]

        if action == "move":
            move_player(player, world)
        elif action == "description":
            locations = world.locations[player.current_location]
            print(f"\n{locations['name']}\n{locations['description']}")
        elif action == "inventory":
            item = show_inventory(player)

            if item:
                if getattr(item, "is_weapon", False):
                    if player.equip_weapon(item):
                        print(f"\nВы экипировали: {item.name}")
                    else:
                        print(f"\n{player.get_weapon_equip_error(item) or (item.name + ' нельзя экипировать сейчас.')}")
                elif get_item_category(item) == "armor":
                    if player.equip_armor(item):
                        print(f"\nВы экипировали: {item.name}")
                    else:
                        print(f"\n{item.name} нельзя экипировать сейчас.")
                elif item.use(player):
                    player.inventory.remove_item(item)
                    print(f"\nВы использовали: {item.name}")
                else:
                    print(f"\n{item.name} нельзя использовать сейчас.")
            input("\nНажмите Enter...", kind="return")
        elif action == "unequip":
            if player.unequip_weapon():
                print("\nВы сняли оружие.")
            else:
                print("\nНе удалось снять оружие.")
            input("\nНажмите Enter...", kind="return")
        elif action == "hunt":
            hunt_optional_enemies(player, player.current_location, world)
        elif action == "chest":
            open_location_chest(player, world)
        elif action == "ground_loot":
            show_ground_loot(player, world, player.current_location)
        elif action == "loot_filter":
            configure_loot_filter(player)
        elif action.startswith("npc:"):
            npc = get_npc(action.split(":", 1)[1])
            if npc is not None:
                interact_with_npc(player, npc)
        elif action == "exit":
            print("Игра завершена")
            break
            

def move_player(player, world): # Функция перемещения
        paths = world.show_paths(player.current_location)
        if not paths:
            print("Нет доступных путей из этой локации")
            return

        print("\nКуда хотите пойти?")
        for i, (location_id, desc) in enumerate(paths.items()):
            print(f"{i + 1}. {desc}")

        print("0. Назад")

        choice = input("\nВыберите путь (номер): ")

        if choice == "0":
            return

        if choice.isdigit():
            index = int(choice) - 1
            path_ids = list(paths.keys())
            if 0 <= index < len(path_ids):
                unavailable_message = world.get_unavailable_message(
                    path_ids[index]
                )
                if unavailable_message:
                    print(f"\n{unavailable_message}")
                    input("\nНажмите Enter, чтобы продолжить...", kind="pause")
                    return
            new_location = world.move(player.current_location, index)
            if new_location == player.current_location:
                print("Неверный выбор, Вы остаетесь на месте")
            player.current_location = new_location
            print(f"\nВы переместились в {world.locations[new_location]['name']}")
            handle_encounter(player, new_location, world)

def get_location_menu_options(world, location_id):
    options = [
        ("move", "Переместиться"),
        ("description", "Описание локации"),
        ("inventory", "Открыть инвентарь"),
        ("unequip", "Снять оружие"),
    ]
    for npc_id in world.get_location_npc_ids(location_id):
        npc = get_npc(npc_id)
        if npc is not None:
            options.append((f"npc:{npc.id}", f"Поговорить: {npc.name}"))
    if world.can_hunt_optional_enemies(location_id):
        options.append(("hunt", "Добить оставшихся врагов"))
    elif world.is_chest_available(location_id):
        options.append(("chest", "Открыть сундук"))
    if world.get_ground_loot(location_id):
        options.append(("ground_loot", "Выпавшие предметы"))
    options.append(("loot_filter", "Настроить лут-фильтр"))
    options.append(("exit", "Выйти из игры"))
    return options

def interact_with_npc(player, npc):
    if isinstance(npc, Merchant):
        trade_with_merchant(player, npc)
        return True
    return False


def open_location_chest(player, world):
    reward = claim_location_chest(
        player,
        player.current_location,
        world,
    )
    if reward is None:
        print("\nНе удалось открыть сундук. Проверьте свободное место в инвентаре.")
    else:
        weapon = reward["weapon"]
        if reward["stored_in_location"]:
            print(f"\nОружие оставлено в локации: {weapon.display_name}")
        else:
            print(f"\nВы получили оружие: {weapon.display_name}")
        print(f"Редкость: {weapon.rarity.title}")
        print(f"Золото: {reward['gold']}")
    input("\nНажмите Enter, чтобы продолжить...", kind="pause")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Axe and Sword")
    parser.add_argument("--cli", action="store_true", help="Играть в терминале")
    args = parser.parse_args()
    if args.cli:
        start_game()
    else:
        from gui import launch
        launch()



