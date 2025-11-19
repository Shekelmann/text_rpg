from classes import Enemy, Item, Damage_type
from player import Player, Inventory
from world import World
from weapon import Weapon, Rarity
from objects import sword, goblin_lvl_1, skeleton_lvl_1
from battle import player_turn, enemy_turn, battle

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это пре-альфа версия ролевой игры в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    
    # Вводим имя
    name = input("Введите имя героя: ")
    
    # Создаем игрока
    player = Player(name, sword)
    
    # Создаем мир
    world = World()
    current_location = "village" # Текущая локация
    paths = world.show_paths(current_location)

    # Игровой цикл
    while True:
    	location = world.get_location(current_location)
    	print("\n=====================")
    	print(f"Текущая локация: {location['name']}")
    	print(location["description"])
    	print("\nВыберите действие: ")
    	print("\n1. Переместиться")
    	print("\n2. Открыть инвентарь")
    	print("\n3. Выйти из игры")
    	
    	choice = input("\nВаш выбор: ").strip()
    	
    	if choice == "1":
    		# нужно связать функцию show_paths с выбором и перемещением
    		#if choice == "1":

    	elif choice == "3":
    		print("Игра завершена")
    		break



if __name__ == "__main__":
    start_game()



