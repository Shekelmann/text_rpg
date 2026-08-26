from enemy import Enemy, Damage_type
from player import Player
from item import Inventory, Item 
from world import World
from weapon import Weapon, Rarity
from objects import WEAPONS, ENEMIES, STARTER_WEAPON
from battle import player_turn, enemy_turn, battle
#from enemy_generator import generate_enemy
from interface import show_player_status
from encounter import handle_encounter

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это пре-альфа версия ролевой игры в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    
    name = input("Введите имя героя: ") # Вводим имя
    player = Player(name, STARTER_WEAPON) # Создаем игрока
    
    # Создаем мир
    world = World()
    player.current_location = "village"
    paths = world.show_paths(player.current_location)

    # Игровой цикл
    while True:
        show_player_status(player)
        locations = world.locations.get(player.current_location)
        print("\n=====================")
        print(f"Текущая локация: {locations['name']}")
        print("\n1. Переместиться")
        print("\n2. Описание локации")
        print("\n3. Открыть инвентарь")
        print("\n4. Выйти из игры")
        
        choice = input("\nВыберите действие: ")
        if choice == "1":
            move_player(player, world)
        elif choice == "2":
            locations = world.locations[player.current_location]
            print(f"\n{locations['name']}\n{locations['description']}")
        elif choice == "3":
            player.inventory.show_inventory()
        elif choice == "4":
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

        choice = input("\nВыберите путь (номер): ")
        if choice.isdigit():
            index = int(choice) - 1
            new_location = world.move(player.current_location, index)
            if new_location == player.current_location:
                print("Неверный выбор, Вы остаетесь на месте")
            player.current_location = new_location
            print(f"\nВы переместились в {world.locations[new_location]['name']}")
            handle_encounter(player, new_location)

if __name__ == "__main__":
    start_game()



