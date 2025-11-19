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

