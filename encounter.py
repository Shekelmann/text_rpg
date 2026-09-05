import random

from battle import battle
from enemy import Enemy
from interface import choose_optional_enemy
from objects import ENEMIES, get_loot_table
from world import LOCATION_ENEMIES, RARITY_CHANCES


def create_enemy(enemy_id, player, rarity="common"):
    enemy_data = ENEMIES[enemy_id]
    enemy = Enemy(
        enemy_data["name"],
        enemy_data["health"],
        enemy_data["min_damage"],
        enemy_data["max_damage"],
        enemy_data["crit_chance"],
        enemy_data["damage_type"],
    )
    enemy.loot = get_loot_table(enemy_id)
    enemy.gold = enemy_data.get("gold", (0, 0))
    enemy.scale_with_level(player.level, rarity=rarity)
    return enemy


def handle_encounter(player, location, world):
    if location not in LOCATION_ENEMIES:
        return False

    state = world.get_combat_state(location)
    if state["main_encounter_completed"]:
        return False

    rarity = random.choices(
        list(RARITY_CHANCES.keys()),
        weights=RARITY_CHANCES.values(),
    )[0]
    enemy_id = random.choice(LOCATION_ENEMIES[location][rarity])
    enemy = create_enemy(enemy_id, player, rarity)

    if battle(player, enemy):
        world.complete_main_encounter(location)
        return True
    return False


def hunt_optional_enemies(player, location, world):
    while world.can_hunt_optional_enemies(location):
        enemy_ids = world.get_optional_enemies(location)
        enemy_names = [ENEMIES[enemy_id]["name"] for enemy_id in enemy_ids]
        enemy_index = choose_optional_enemy(enemy_names)
        if enemy_index is None:
            return

        enemy = create_enemy(enemy_ids[enemy_index], player)
        if battle(player, enemy):
            world.defeat_optional_enemy(location, enemy_index)
        else:
            return
