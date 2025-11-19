from classes import *
from objects import *

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это пре-альфа версия ролевой игры в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    
    # Вводим имя
    name = input("Введите имя героя: ")
    
    # Создаем игрока
    player = Player(name, sword)
    
    # Создаем мир
    world = World()
    current_location = "village"

    # Игровой цикл
    while True:
    	location = world.get_location(current_location)
    	print("\n=====================")
    	print(f"Текущая локация: {location['name']}")
    	print(location["description"])

    	print("\nКуда хотите пойти?")
    	print("- exit: Выйти из игры")
    	choice = input("\nВаш выбор: ").strip()
    	
    	if choice == "exit":
    		print("Игра завершена")
    		break


if __name__ == "__main__":
    start_game()



