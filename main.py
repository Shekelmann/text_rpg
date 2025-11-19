from classes import *
from objects import *

# Структура хода
def player_turn(player, enemy):
	print("\nВаш ход:")
	print("1 - Атака")
	print("2 - Пропустить ход")

	choice = input("Выберите действие: ")

	if choice == "1":
		damage, crit = player.attack()
		enemy.take_damage(damage)
		if crit:
			print(f"Критический удар! Вы нанесли {damage} урона.")
		else:
			print(f"Вы нанесли {damage} урона.")
	else:
		("Вы пропустили ход.")

def enemy_turn(enemy, player):
    print(f"\n{enemy.name} атакует!")
    damage = enemy.attack()
    player.take_damage(damage)
    print(f"{enemy.name} наносит {damage} урона!")

def battle(player, enemy):
    print(f"\nВы встретили врага: {enemy.name} (HP: {enemy.health})!\n")

    while player.is_alive() and enemy.is_alive():
        print(f"Ваше HP: {player.health} | HP врага: {enemy.health}")
        player_turn(player, enemy)

        if not enemy.is_alive():
            print(f"\nВы победили {enemy.name}!\n")
            break

        enemy_turn(enemy, player)

    if not player.is_alive():
        print("\nВы погибли... Игра окончена.\n")

# Начало игры
def start_game():
    print("Добро пожаловать в Axe and Sword! Это ролевая игра в фэнтезийном мире, где Вам предстоит сражаться с ужасными монстрами")
    name = input("Введите имя героя: ")
    player = Player(name, sword)
    enemy = Enemy("Гоблин", 15, 1, 1, 6, 0.10, 1, 1)

    battle(player, enemy)

if __name__ == "__main__":
    start_game()