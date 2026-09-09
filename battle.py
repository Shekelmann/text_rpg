from game_io import input, print
import random
import time
from effects import ATTACK_ACTION, NON_ATTACK_ACTION
from interface import allocate_stat_points, show_battle_screen
from objects import generate_loot
from rarity import Rarity
from player import Player
from enemy import Enemy

COMBAT_MESSAGE_DELAY = 0.6

ATTACK_ACTION_KIND = "attack"
CONSUMABLE_ACTION_KIND = "consumable"
MAGIC_ACTION_KIND = "magic"


class PlayerTurnState:
    def __init__(self, available_actions):
        self.available_actions = set(available_actions)
        self.used_actions = set()
        self.finished = False

    def can_use(self, action):
        return action in self.available_actions and action not in self.used_actions

    def use(self, action):
        if not self.can_use(action):
            return False
        self.used_actions.add(action)
        return True

    def finish(self):
        self.finished = True

    @property
    def is_complete(self):
        return self.finished or self.used_actions >= self.available_actions


def create_player_turn_state(player):
    available_actions = {ATTACK_ACTION_KIND}
    if any(item.use_in_combat for item in player.inventory.items):
        available_actions.add(CONSUMABLE_ACTION_KIND)
    return PlayerTurnState(available_actions)


def get_player_turn_actions(turn_state):
    actions = []
    if turn_state.can_use(ATTACK_ACTION_KIND):
        actions.append("1 - Атака")
    if not turn_state.is_complete:
        actions.append("2 - Завершить ход")
    if turn_state.can_use(CONSUMABLE_ACTION_KIND):
        actions.append("3 - Использовать зелье")
    return actions

# Структура хода
def player_turn(player, enemy, messages=None, turn_state=None):
    turn_state = turn_state or create_player_turn_state(player)
    choice = input("Выберите действие: ")

    if choice == "1":
        if not turn_state.use(ATTACK_ACTION_KIND):
            return ["Атака в этом ходу уже использована."]
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
        turn_state.finish()
        return ["Вы завершаете ход."]
    
    if choice == "3":
        if CONSUMABLE_ACTION_KIND not in turn_state.available_actions:
            return ["У вас нет зелий."]
        if CONSUMABLE_ACTION_KIND in turn_state.used_actions:
            return ["Расходник в этом ходу уже использован."]
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
                    turn_state.use(CONSUMABLE_ACTION_KIND)
                    player.inventory.remove_item(potion)
                    turn_messages = [f"Вы используете {potion.name}."]
                    turn_messages.extend(
                        player.trigger_action_effects(NON_ATTACK_ACTION).messages
                    )
                    return turn_messages
                return [f"{potion.name} нельзя использовать сейчас."]

        return ["Неверный выбор зелья."]

    return ["Неверный выбор."]

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


def format_dropped_item(item):
    return (
        f"{getattr(item, 'display_name', item.name)} "
        f"[{getattr(item, 'rarity', Rarity.COMMON).title}]"
    )


def distribute_loot(player, items, world=None, location=None):
    hidden_count = 0
    for item in items:
        stored = player.inventory.add_item(item)
        if not stored and world is not None and location is not None:
            stored = world.add_ground_loot(location, item)

        if not player.loot_filter.matches(item):
            hidden_count += 1
        elif item in player.inventory.items:
            print(f"Вы получили: {format_dropped_item(item)}")
        elif stored:
            print(f"Оставлено в локации: {format_dropped_item(item)}")
        else:
            print(f"Не удалось сохранить предмет: {format_dropped_item(item)}")

    if hidden_count:
        print(f"Скрыто предметов: {hidden_count}.")


def finish_victory(player, enemy, messages, world=None, location=None):
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

    distribute_loot(
        player,
        generate_loot(enemy.loot, enemy_level=enemy.level),
        world,
        location,
    )
    input("\nНажмите Enter, чтобы продолжить...", kind="pause")
    return True

def battle(player, enemy, world=None, location=None):
    messages = [f"Вы встретили противника «{enemy.name}»."]

    while player.is_alive() and enemy.is_alive():
        player_effects = player.trigger_turn_start_effects()
        if player_effects.messages:
            messages = []
            show_messages(player, enemy, messages, player_effects.messages)
        if not player.is_alive():
            break

        turn_state = create_player_turn_state(player)
        while not turn_state.is_complete:
            show_battle_screen(
                player,
                enemy,
                messages,
                actions=get_player_turn_actions(turn_state),
            )
            turn_messages = player_turn(
                player,
                enemy,
                messages,
                turn_state,
            )
            messages = []
            show_messages(player, enemy, messages, turn_messages)

            if not enemy.is_alive():
                return finish_victory(player, enemy, messages, world, location)
            if not player.is_alive():
                break

        if not player.is_alive():
            break

        enemy_effects = enemy.trigger_turn_start_effects()
        if enemy_effects.messages:
            show_messages(player, enemy, messages, enemy_effects.messages)
        if not enemy.is_alive():
            return finish_victory(player, enemy, messages, world, location)

        show_messages(player, enemy, messages, enemy_turn(enemy, player))
        if not enemy.is_alive():
            return finish_victory(player, enemy, messages, world, location)

    if not player.is_alive():
        show_messages(player, enemy, messages, ["Вы проиграли бой."])
        player.after_death()
        return False

    return False


