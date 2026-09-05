import random
import time
from interface import allocate_stat_points, show_battle_screen
from objects import generate_loot
from player import Player
from enemy import Enemy

COMBAT_MESSAGE_DELAY = 0.6

# Структура хода
def player_turn(player, enemy, messages=None):
    choice = input("Выберите действие: ")

    if choice == "1":
        damage, crit = player.attack()
        enemy.take_damage(damage)
        turn_messages = [
            f"Вы наносите противнику «{enemy.name}» {damage} урона."
        ]
        if crit:
            turn_messages.append("Критический удар!")
        return turn_messages

    if choice == "2":
        return ["Вы пропускаете ход."]
    
    if choice == "3":
        potions = [
            item for item in player.inventory.items
            if item.item_type == "potion"
        ]

        if not potions:
            return ["У вас нет зелий."]

        potion_actions = [
            f"{i} - {potion.name}"
            for i, potion in enumerate(potions, 1)
        ]
        show_battle_screen(
            player,
            enemy,
            messages,
            actions=potion_actions,
        )

        potion_choice = input("Выберите зелье: ")

        if potion_choice.isdigit():
            index = int(potion_choice) - 1

            if 0 <= index < len(potions):
                potion = potions[index]

                if potion.use(player):
                    player.inventory.remove_item(potion)
                    return [f"Вы используете {potion.name}."]
                return [f"{potion.name} нельзя использовать сейчас."]

        return ["Неверный выбор зелья."]

    return ["Неверный выбор. Ход пропущен."]

def enemy_turn(enemy, player):
    damage = enemy.attack()
    if random.random() < player.get_dodge_chance():
        return [f"Вы уклоняетесь от атаки «{enemy.name}»."]
    player.take_damage(damage, enemy.damage_type)
    return [f"{enemy.name} наносит вам {damage} урона."]

def show_messages(player, enemy, messages, new_messages):
    for message in new_messages:
        messages.append(message)
        show_battle_screen(player, enemy, messages)
        time.sleep(COMBAT_MESSAGE_DELAY)

def battle(player, enemy):
    messages = [f"Вы встретили противника «{enemy.name}»."]

    while player.is_alive() and enemy.is_alive():
        show_battle_screen(player, enemy, messages)
        turn_messages = player_turn(player, enemy, messages)
        messages = []
        show_messages(player, enemy, messages, turn_messages)

        if not enemy.is_alive():
            show_messages(
                player,
                enemy,
                messages,
                [f"Вы победили противника «{enemy.name}»!"],
            )

            #опыт
            player.add_exp(enemy.exp_reward)
            allocate_stat_points(player)

            #золото
            gold = random.randint(enemy.gold[0], enemy.gold[1])
            player.gold += gold
            print(f"Вы получили {gold} золота")

            #лут
            for item in generate_loot(enemy.loot):
                if player.inventory.add_item(item):
                    print(f"Вы получили: {item.name}")
                else:
                    print(f"{item.name} не поместился в инвентарь.")
            input("\nНажмите Enter, чтобы продолжить...")
            return True

        show_messages(player, enemy, messages, enemy_turn(enemy, player))

    if not player.is_alive():
        show_messages(player, enemy, messages, ["Вы проиграли бой."])
        player.after_death()
        return False

    return False


