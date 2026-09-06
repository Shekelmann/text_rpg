import random
import time
from effects import ATTACK_ACTION, NON_ATTACK_ACTION
from interface import allocate_stat_points, show_battle_screen
from objects import generate_loot
from player import Player
from enemy import Enemy

COMBAT_MESSAGE_DELAY = 0.6

# Структура хода
def player_turn(player, enemy, messages=None):
    choice = input("Выберите действие: ")

    if choice == "1":
        damage, crit = player.attack(enemy)
        enemy.take_damage(damage)
        # Player attacks currently always hit; keep on-hit separate from damage rolls.
        if player.main_hand:
            player.main_hand.on_hit(enemy)
        turn_messages = [
            f"Вы наносите противнику «{enemy.name}» {damage} урона."
        ]
        if crit:
            turn_messages.append("Критический удар!")
        turn_messages.extend(
            player.trigger_action_effects(ATTACK_ACTION).messages
        )
        return turn_messages

    if choice == "2":
        turn_messages = ["Вы пропускаете ход."]
        turn_messages.extend(
            player.trigger_action_effects(NON_ATTACK_ACTION).messages
        )
        return turn_messages
    
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
                    turn_messages = [f"Вы используете {potion.name}."]
                    turn_messages.extend(
                        player.trigger_action_effects(NON_ATTACK_ACTION).messages
                    )
                    return turn_messages
                return [f"{potion.name} нельзя использовать сейчас."]

        return ["Неверный выбор зелья."]

    return ["Неверный выбор. Ход пропущен."]

def enemy_turn(enemy, player):
    damage = enemy.attack()
    if random.random() < player.get_dodge_chance():
        turn_messages = [f"Вы уклоняетесь от атаки «{enemy.name}»."]
    else:
        received_damage = player.take_damage(damage, enemy.damage_type)
        turn_messages = [
            f"{enemy.name} наносит вам {received_damage} урона."
        ]
    turn_messages.extend(
        enemy.trigger_action_effects(ATTACK_ACTION).messages
    )
    return turn_messages

def show_messages(player, enemy, messages, new_messages):
    for message in new_messages:
        messages.append(message)
        show_battle_screen(player, enemy, messages)
        time.sleep(COMBAT_MESSAGE_DELAY)


def finish_victory(player, enemy, messages):
    show_messages(
        player,
        enemy,
        messages,
        [f"Вы победили противника «{enemy.name}»!"],
    )

    player.add_exp(enemy.exp_reward)
    allocate_stat_points(player)

    gold = random.randint(enemy.gold[0], enemy.gold[1])
    player.gold += gold
    print(f"Вы получили {gold} золота")

    for item in generate_loot(enemy.loot):
        if player.inventory.add_item(item):
            print(f"Вы получили: {item.name}")
        else:
            print(f"{item.name} не поместился в инвентарь.")
    input("\nНажмите Enter, чтобы продолжить...")
    return True

def battle(player, enemy):
    messages = [f"Вы встретили противника «{enemy.name}»."]

    while player.is_alive() and enemy.is_alive():
        player_effects = player.trigger_turn_start_effects()
        if player_effects.messages:
            messages = []
            show_messages(player, enemy, messages, player_effects.messages)
        if not player.is_alive():
            break

        show_battle_screen(player, enemy, messages)
        turn_messages = player_turn(player, enemy, messages)
        messages = []
        show_messages(player, enemy, messages, turn_messages)

        if not enemy.is_alive():
            return finish_victory(player, enemy, messages)
        if not player.is_alive():
            break

        enemy_effects = enemy.trigger_turn_start_effects()
        if enemy_effects.messages:
            show_messages(player, enemy, messages, enemy_effects.messages)
        if not enemy.is_alive():
            return finish_victory(player, enemy, messages)

        show_messages(player, enemy, messages, enemy_turn(enemy, player))
        if not enemy.is_alive():
            return finish_victory(player, enemy, messages)

    if not player.is_alive():
        show_messages(player, enemy, messages, ["Вы проиграли бой."])
        player.after_death()
        return False

    return False


