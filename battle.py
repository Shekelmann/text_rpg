import random
from interface import show_enemy_status
from objects import ITEMS

#использование зелий
def use_potion(player):
	print("\n=== Зелья ===")

	potions = []

	for item in player.inventory.items:
		if item.item_type == "potion":
			potions.append(item)

	if not potions:
		print("У вас нет зелий.")
		return

	for i, potion in enumerate(potions, 1):
		print(f"{i}. {potion.name}")

	print("0. Назад")

	choice = input("Выберите зелье: ")

	if choice == "0":
		return

	if choice.isdigit():
		index = int(choice) - 1

		if 0 <= index < len(potions):
			potion = potions[index]

			if potion.name == "Зелье лечения":
				player.health = min(
					player.health + 30,
            		player.max_health
				)

				player.inventory.items.remove(potion)

				print(f"Вы использовали {potion.name}.")
				print(f"HP: {player.health} / {player.max_health}")

# Структура хода
def player_turn(player, enemy):
	print("\nВаш ход:")
	print("1 - Атака")
	print("2 - Пропустить ход")
	print("3 - Использовать зелье")


	choice = input("Выберите действие: ")

	if choice == "1":
		damage, crit = player.attack()
		enemy.take_damage(damage)
		if crit:
			print(f"Критический удар! Вы нанесли {damage} урона.")
		else:
			print(f"Вы нанесли {damage} урона.")
	
	elif choice == "3":
		use_potion(player)
	else:
		("Вы пропустили ход.")

def enemy_turn(enemy, player):
    print(f"\n{enemy.name} атакует!")
    damage = enemy.attack()
    player.take_damage(damage)
    print(f"{enemy.name} наносит {damage} урона!")

def battle(player, enemy):
    print(f"\nВы встретили врага: {enemy.name} (HP: {enemy.health})!\n")
    show_enemy_status(enemy)

    while player.is_alive() and enemy.is_alive():
        print(f"Ваше HP: {player.health} | HP врага: {enemy.health}")
        player_turn(player, enemy)

        if not enemy.is_alive():
            print(f"\nВы победили {enemy.name}!\n")

            #опыт
            player.exp += enemy.exp_reward
            print(f"Вы получили {enemy.exp_reward} очков опыта")

            #золото
            gold = random.randint(enemy.gold[0], enemy.gold[1])
            player.gold += gold
            print(f"Вы получили {gold} золота")

            #лут
            for item_id, chance in enemy.loot.items():
            	if random.random() < chance:
            		item = ITEMS[item_id]
            		player.inventory.add_item(item)
            break

        enemy_turn(enemy, player)

    if not player.is_alive():
        print("\nВы погибли... Игра окончена.\n")

