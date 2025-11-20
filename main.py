from classes import Enemy, Damage_type
from player import Player
from item import Inventory, Item 
from world import World
from weapon import Weapon, Rarity
from objects import WEAPONS, ENEMIES
from battle import player_turn, enemy_turn, battle
from enemy_generator import generate_enemy

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это пре-альфа версия ролевой игры в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    
    # Вводим имя
    name = input("Введите имя героя: ")
    weapon = Weapon("Простой меч", 2, 5, 0.10, "Одноручное", Damage_type.PHYSICAL)
    # Создаем игрока
    player = Player(name, weapon)
    
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
    		exits = world.show_paths(current_location)

    	if choice == "3":
    		print("Игра завершена")
    		break
    	#if choice == "1":
    		# нужно связать функцию show_paths с выбором и перемещением
    		#if choice == "1":
    	#elif choice == "2":
    		#print

    	#elif choice == "3":
    		#print("Игра завершена")
    		#break



if __name__ == "__main__":
    start_game()



