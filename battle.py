import random
from interface import show_enemy_status
from objects import create_item
from player import Player
from enemy import Enemy

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
        potions = [
            item for item in player.inventory.items
            if item.item_type == "potion"
        ]

        if not potions:
            print("У вас нет зелий.")
            return

        for i, potion in enumerate(potions, 1):
            print(f"{i} - {potion.name}")

        potion_choice = input("Выберите зелье: ")

        if potion_choice.isdigit():
            index = int(potion_choice) - 1

            if 0 <= index < len(potions):
                potion = potions[index]

                if potion.use(player):
                    player.inventory.remove_item(potion)
                    print(f"Вы использовали {potion.name}.")
                else:
                    print(f"{potion.name} не может быть использовано сейчас.")
        

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
            player.add_exp(enemy.exp_reward)

            #золото
            gold = random.randint(enemy.gold[0], enemy.gold[1])
            player.gold += gold
            print(f"Вы получили {gold} золота")

            #лут
            for item_id, chance in enemy.loot.items():
                if random.random() < chance:
                    item = create_item(item_id)

                    if player.inventory.add_item(item):
                        print(f"Вы получили: {item.name}")
                    else:
                        print(f"{item.name} не поместился в инвентарь.")
            input("\nНажмите Enter, чтобы продолжить...")
            break

        enemy_turn(enemy, player)

    if not player.is_alive():
        player.after_death()


