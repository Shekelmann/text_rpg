from game_io import input, print
import math
import random
import time
from damage import Damage_type
from effects import ATTACK_ACTION, NON_ATTACK_ACTION, CombatAction
from interface import allocate_stat_points, show_battle_screen
from objects import generate_loot
from rarity import Rarity
from player import Player
from enemy import Enemy
from combat_hit import resolve_hit

COMBAT_MESSAGE_DELAY = 0.6

ATTACK_ACTION_KIND = "attack"
CONSUMABLE_ACTION_KIND = "consumable"
MAGIC_ACTION_KIND = "magic"
BASE_ACTION_POINTS = 3
ACTION_COSTS = {
    ATTACK_ACTION_KIND: 2,
    CONSUMABLE_ACTION_KIND: 1,
}


class PlayerTurnState:
    def __init__(self, available_actions, action_points=BASE_ACTION_POINTS):
        self.available_actions = set(available_actions)
        self.used_actions = set()
        self.used_spell_ids = set()
        self.action_points = action_points
        self.base_action_points = action_points
        self.finished = False

    def can_use(self, action, cost=None):
        if self.finished or action not in self.available_actions:
            return False
        if cost is None:
            cost = ACTION_COSTS.get(action, 0)
        return self.action_points >= cost

    def use(self, action, cost=None):
        if cost is None:
            cost = ACTION_COSTS.get(action, 0)
        if not self.can_use(action, cost):
            return False
        self.used_actions.add(action)
        self.action_points -= cost
        return True

    def gain(self, amount):
        self.action_points += amount

    def finish(self):
        self.finished = True

    @property
    def is_complete(self):
        return self.finished


def cast_spell_action(player, target, spell_id, turn_state, *, action, one_shot=False):
    """Cast through the existing turn-action and status-effect policies."""
    from spell import CastResult
    if not isinstance(action, CombatAction):
        return CastResult(False, "Не задан тип магического действия.")
    spell = next((spell for spell, scroll in get_combat_spells(player)
                  if spell.id == spell_id and scroll == one_shot), None)
    if spell is None:
        return CastResult(False, "Заклинание не изучено.")
    if spell_id == "slow_time" and spell_id in turn_state.used_spell_ids:
        return CastResult(False, "«Замедлить время» уже использовано в этом ходу.")
    if not turn_state.can_use(MAGIC_ACTION_KIND, spell.action_cost):
        return CastResult(False, "Магическое действие сейчас недоступно.")
    result = player.cast_spell(spell_id, target, one_shot=one_shot)
    if result.success:
        turn_state.use(MAGIC_ACTION_KIND, spell.action_cost)
        turn_state.gain(spell.action_points_gain)
        turn_state.used_spell_ids.add(spell_id)
        effects = player.trigger_action_effects(action)
        return CastResult(True, damage=result.damage,
                          messages=result.messages + tuple(effects.messages))
    return result


def create_player_turn_state(player):
    available_actions = {ATTACK_ACTION_KIND}
    if any(player.get_flask_count(resource) for resource in ("hp", "mp")):
        available_actions.add(CONSUMABLE_ACTION_KIND)
    if player.spellbook.learned or player.spellbook.scrolls:
        available_actions.add(MAGIC_ACTION_KIND)
    return PlayerTurnState(available_actions)


def has_usable_action(player, enemy, turn_state):
    if turn_state.finished or not player.is_alive() or not enemy.is_alive():
        return False
    if turn_state.can_use(ATTACK_ACTION_KIND):
        return True
    if turn_state.can_use(CONSUMABLE_ACTION_KIND):
        if any(player.can_use_flask(key) for key in ("hp", "mp")):
            return True
    if MAGIC_ACTION_KIND in turn_state.available_actions:
        options = get_combat_spell_options(player, enemy, turn_state)
        return any(option["enabled"] for option in options.values())
    return False


def get_player_turn_actions(turn_state, player=None, enemy=None):
    actions = []
    if turn_state.can_use(ATTACK_ACTION_KIND):
        actions.append("1 - Атака — 2 ОД")
    if not turn_state.is_complete:
        actions.append("2 - Завершить ход")
    flask_available = turn_state.can_use(CONSUMABLE_ACTION_KIND)
    if player is not None and flask_available:
        flask_available = any(player.can_use_flask(key) for key in ("hp", "mp"))
    if flask_available:
        actions.append("3 - Использовать флягу — 1 ОД")
    magic_available = turn_state.can_use(MAGIC_ACTION_KIND)
    if player is not None and enemy is not None and magic_available:
        magic_available = any(option["enabled"] for option in
                              get_combat_spell_options(player, enemy, turn_state).values())
    if magic_available:
        actions.append("4 - Заклинание")
    return actions


def get_combat_spells(player):
    spells = [(spell, False) for spell in player.spellbook.learned]
    spells.extend((spell, True) for spell, _count in player.spellbook.scrolls)
    return spells

def get_combat_spell_options(player, enemy, turn_state=None):
    from gui_views import spellbook_snapshot
    snapshot = spellbook_snapshot(player)
    entries = (*snapshot["learned"], *snapshot["scrolls"])
    options = {}
    for index, ((spell, one_shot), entry) in enumerate(zip(get_combat_spells(player), entries), 1):
        reason = player.spellbook.check(player, spell.id, enemy, one_shot=one_shot)
        if not reason and turn_state is not None:
            if spell.id == "slow_time" and spell.id in turn_state.used_spell_ids:
                reason = "Уже использовано в этом ходу."
            elif not turn_state.can_use(MAGIC_ACTION_KIND, spell.action_cost):
                reason = "Недостаточно ОД."
        options[str(index)] = dict(
            tooltip=tuple(entry["details"].splitlines()),
            enabled=not reason,
            reason=reason,
        )
    return options


# Структура хода
def player_turn(player, enemy, messages=None, turn_state=None):
    turn_state = turn_state or create_player_turn_state(player)
    choice = input("Выберите действие: ", kind="battle")

    if choice.startswith("flask:"):
        resource = choice.split(":", 1)[1]
        if not turn_state.can_use(CONSUMABLE_ACTION_KIND):
            return ["Недостаточно ОД."]
        if not player.use_flask(resource):
            return ["Фласку нельзя использовать сейчас."]
        turn_state.use(CONSUMABLE_ACTION_KIND)
        return [f"Вы используете {resource.upper()}-фласку.",
                *player.trigger_action_effects(NON_ATTACK_ACTION).messages]

    if choice == "1":
        if not turn_state.use(ATTACK_ACTION_KIND):
            return ["Недостаточно ОД."]
        turn_messages = []
        for index, weapon in enumerate(player.attack_weapons()):
            if not enemy.is_alive():
                break
            damage_type = weapon.damage_type if weapon else Damage_type.PHYSICAL
            result = resolve_hit(
                enemy,
                lambda: player.attack(enemy) if index == 0 else player.attack(enemy, weapon=weapon),
                damage_type,
                on_hit=weapon.on_hit if weapon else None,
            )
            if not result.hit:
                turn_messages.append(f"Противник «{enemy.name}» уклоняется от вашей атаки.")
                continue
            turn_messages.append(f"Вы наносите противнику «{enemy.name}» {result.damage} урона.")
            if result.critical:
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
            return ["У вас нет доступных зарядов фляг."]
        if not turn_state.can_use(CONSUMABLE_ACTION_KIND):
            return ["Недостаточно ОД."]
        resources = [key for key in ("hp", "mp") if player.can_use_flask(key)]
        if not resources:
            return ["Нет доступных зарядов фляг."]
        names = {"hp": "HP-фляга", "mp": "MP-фляга"}
        flask_actions = [
            f"{i} - {names[resource]} — 1 ОД "
            f"(осталось: {player.get_flask_count(resource)})"
            for i, resource in enumerate(resources, 1)
        ]
        flask_actions.append("0 - Назад")
        show_battle_screen(
            player,
            enemy,
            messages,
            actions=flask_actions,
            action_points=turn_state.action_points,
        )

        flask_choice = input("Выберите флягу: ", kind="flasks")

        if flask_choice == "0":
            return ["Вы возвращаетесь к выбору действия."]

        if flask_choice.isdigit():
            index = int(flask_choice) - 1

            if 0 <= index < len(resources):
                resource = resources[index]
                if player.use_flask(resource):
                    turn_state.use(CONSUMABLE_ACTION_KIND)
                    turn_messages = [f"Вы используете {names[resource]}."]
                    turn_messages.extend(
                        player.trigger_action_effects(NON_ATTACK_ACTION).messages
                    )
                    return turn_messages
                return [f"{names[resource]} сейчас недоступна."]

        return ["Неверный выбор фляги."]

    if choice == "4":
        if MAGIC_ACTION_KIND not in turn_state.available_actions:
            return ["У вас нет доступных заклинаний."]
        spells = get_combat_spells(player)
        if not spells:
            return ["У вас нет доступных заклинаний."]
        spell_actions = []
        scroll_counts = dict(
            (spell.id, count) for spell, count in player.spellbook.scrolls
        )
        for index, (spell, one_shot) in enumerate(spells, 1):
            cost = f"{spell.cost} MP" if spell.resource == "mana" else "бесплатно"
            suffix = f" · свиток ×{scroll_counts[spell.id]}" if one_shot else ""
            spell_actions.append(
                f"{index} - {spell.name} — {spell.action_cost} ОД ({cost}{suffix})"
            )
        spell_actions.append("0 - Назад")
        show_battle_screen(player, enemy, messages, actions=spell_actions,
                           spell_options=get_combat_spell_options(player, enemy, turn_state),
                           action_points=turn_state.action_points)
        spell_choice = input("Выберите заклинание: ", kind="spells")
        if spell_choice == "0":
            return ["Вы возвращаетесь к выбору действия."]
        if not spell_choice.isdigit():
            return ["Неверный выбор заклинания."]
        index = int(spell_choice) - 1
        if not 0 <= index < len(spells):
            return ["Неверный выбор заклинания."]
        spell, one_shot = spells[index]
        target = player if spell.target == "self" else enemy
        result = cast_spell_action(
            player, target, spell.id, turn_state,
            action=NON_ATTACK_ACTION, one_shot=one_shot,
        )
        return list(result.messages) if result.success else [result.reason]

    return ["Неверный выбор."]

def enemy_turn(enemy, player):
    result = resolve_hit(player, enemy.attack, enemy.damage_type)
    if not result.hit:
        turn_messages = [f"Вы уклоняетесь от атаки «{enemy.name}»."]
    else:
        turn_messages = [
            f"{enemy.name} наносит вам {result.damage} урона."
        ]
        if result.critical:
            turn_messages.append("Критический удар противника!")
    turn_messages.extend(
        enemy.trigger_action_effects(ATTACK_ACTION).messages
    )
    return turn_messages

def show_messages(player, enemy, messages, new_messages, action_points=None):
    for message in new_messages:
        messages.append(message)
        if action_points is None:
            show_battle_screen(player, enemy, messages)
        else:
            show_battle_screen(player, enemy, messages, action_points=action_points)
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

    gold = max(math.ceil(2 * enemy.level * enemy.difficulty),
               random.randint(enemy.gold[0], enemy.gold[1]))
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
            if not has_usable_action(player, enemy, turn_state):
                turn_state.finish()
                break
            show_battle_screen(
                player,
                enemy,
                messages,
                actions=get_player_turn_actions(turn_state, player, enemy),
                action_points=turn_state.action_points,
            )
            turn_messages = player_turn(
                player,
                enemy,
                messages,
                turn_state,
            )
            messages = []
            show_messages(
                player, enemy, messages, turn_messages,
                action_points=turn_state.action_points,
            )

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

        if not enemy_effects.skip_turn:
            show_messages(player, enemy, messages, enemy_turn(enemy, player))
        if not enemy.is_alive():
            return finish_victory(player, enemy, messages, world, location)

    if not player.is_alive():
        show_messages(player, enemy, messages, ["Вы проиграли бой."])
        player.after_death()
        return False

    return False


