"""Reproducible 1v1 reference calculations; no random loot or affixes.

TTK is the exact expected number of discrete actions, including overkill.
Successful-action TTK excludes zero-damage misses; attempt TTK includes Dodge.
This is not a win-probability simulation or a model of consumable use.
"""

from collections import defaultdict
from copy import deepcopy
import json

from character_class import CLASSES
from damage import Damage_type
from encounter import create_enemy
from item import Armor
from objects import WEAPONS
from player import Player


REFERENCE_WEAPONS = {"bruiser": "sword", "daredevil": "sword", "herald": "staff"}
PRIMARY_STATS = {"bruiser": "strength", "daredevil": "dexterity", "herald": "intelligence"}


def reference_player(class_id="bruiser", level=1, weapon_id=None, armor=2):
    weapon = deepcopy(WEAPONS[weapon_id or REFERENCE_WEAPONS[class_id]])
    weapon.level = level
    player = Player("Reference", weapon, CLASSES[class_id])
    player.level = level
    stat = PRIMARY_STATS[class_id]
    setattr(player, stat, getattr(player, stat) + level - 1)
    player.recalculate_max_health(restore_to_full=True)
    if armor:
        item = Armor("Reference armor", armor)
        player.inventory.add_item(item)
        player.equip_armor(item)
    return player


def damage_distribution(minimum, maximum, crit):
    result = defaultdict(float)
    for damage in range(minimum, maximum + 1):
        result[damage] += (1 - crit) / (maximum - minimum + 1)
        result[damage * 2] += crit / (maximum - minimum + 1)
    return dict(result)


def with_dodge(distribution, dodge):
    result = {damage: chance * (1 - dodge) for damage, chance in distribution.items()}
    result[0] = result.get(0, 0) + dodge
    return result


def expected_actions(health, distribution):
    """E[h] = (1 + sum(p[d]*E[max(0,h-d)] for d>0)) / (1-p[0])."""
    positive = [(damage, chance) for damage, chance in distribution.items() if damage > 0 and chance > 0]
    success = sum(chance for damage, chance in positive)
    if not success:
        return float("inf")
    expected = [0.0] * (health + 1)
    for hp in range(1, health + 1):
        expected[hp] = (1 + sum(chance * expected[max(0, hp - damage)]
                                for damage, chance in positive)) / success
    return expected[health]


def mean(distribution):
    return sum(damage * chance for damage, chance in distribution.items())


def opening_spell_rounds(health, attacks, spell_damage, casts):
    """Separate spell action before a weapon action, limited initial MP, no refills."""
    previous = [expected_actions(hp, attacks) for hp in range(health + 1)]
    for _ in range(casts):
        current = [0.0] * (health + 1)
        for hp in range(1, health + 1):
            current[hp] = 1 + sum(p * previous[max(0, hp - spell_damage - d)]
                                  for d, p in attacks.items())
        previous = current
    return previous[health]


def player_distribution(player, enemy):
    # Reference weapons have no affixes. Both daggers, if equipped, form ONE action.
    result = {0: 1.0}
    for weapon in player.attack_weapons():
        assert not weapon.affixes, "Reference model excludes affixes"
        low, high = player.get_attack_damage_range(enemy, weapon)
        crit = player.get_crit_chance(weapon.final_crit_chance)
        hit = with_dodge(damage_distribution(low, high, crit), enemy.get_dodge_chance())
        combined = defaultdict(float)
        for first, p1 in result.items():
            for second, p2 in hit.items():
                combined[first + second] += p1 * p2
        result = dict(combined)
    return result


def enemy_distribution(enemy, player):
    raw = damage_distribution(enemy.min_damage, enemy.max_damage, enemy.crit_chance)
    result = defaultdict(float)
    old_health = player.health
    try:
        for damage, chance in raw.items():
            player.health = 1000000  # Avoid lethal-hit clipping; use real mitigation.
            dealt = player.take_damage(damage, enemy.damage_type)
            assert dealt == int(dealt), "Reference model requires integral mitigation"
            result[int(dealt)] += chance
    finally:
        player.health = old_health
    return with_dodge(dict(result), player.get_dodge_chance())


def successful_distribution(distribution):
    success = sum(p for d, p in distribution.items() if d > 0)
    return {d: p / success for d, p in distribution.items() if d > 0} if success else {0: 1}


def row(enemy_id, level=1, class_id="bruiser", weapon_id=None, armor=2, rarity="common"):
    player = reference_player(class_id, level, weapon_id, armor)
    enemy = create_enemy(enemy_id, level, rarity)
    outgoing = player_distribution(player, enemy)
    incoming = enemy_distribution(enemy, player)
    return {
        "enemy": enemy_id, "level": level, "rarity": rarity,
        "class": class_id, "weapon": weapon_id or REFERENCE_WEAPONS[class_id],
        "player_hp": player.max_health, "armor": armor, "hp": enemy.max_health,
        "avg_damage": mean(successful_distribution(incoming)),
        "player_avg_damage": mean(successful_distribution(outgoing)),
        "dodge": enemy.get_dodge_chance(), "crit": enemy.crit_chance,
        "player_ttk_hits": expected_actions(enemy.max_health, successful_distribution(outgoing)),
        "player_ttk_attempts": expected_actions(enemy.max_health, outgoing),
        "enemy_ttk_hits": expected_actions(player.max_health, successful_distribution(incoming)),
        "enemy_ttk_attempts": expected_actions(player.max_health, incoming),
    }


if __name__ == "__main__":
    from objects import ENEMIES
    print(json.dumps([row(key, level) for level in (1, 3, 6, 10) for key in ENEMIES],
                     ensure_ascii=False, indent=2))
