import random

from battle import battle
from enemy import Enemy
from interface import choose_optional_enemy
from objects import ENEMIES, generate_chest_reward, get_loot_table
from world import LOCATION_ENEMIES, LOCATION_LEVEL_RANGES, get_rarity_chances


def create_enemy(enemy_id, level, rarity="common"):
    if not isinstance(level, int):
        level = level.level
    enemy_data = ENEMIES[enemy_id]
    enemy = Enemy(
        enemy_data["name"],
        enemy_data["health"],
        enemy_data["min_damage"],
        enemy_data["max_damage"],
        enemy_data["crit_chance"],
        enemy_data["damage_type"],
    )
    enemy.id = enemy_id
    enemy.loot = get_loot_table(enemy_id)
    enemy.gold = enemy_data.get("gold", (0, 0))
    enemy.scale_with_level(level, rarity=rarity)
    return enemy


def handle_encounter(player, location, world):
    if location not in LOCATION_ENEMIES:
        return False

    state = world.get_combat_state(location)
    if state["main_encounter_completed"]:
        return False

    rarity_chances = get_rarity_chances(location)
    rarity = random.choices(
        list(rarity_chances.keys()),
        weights=rarity_chances.values(),
    )[0]
    enemy_id = random.choice(LOCATION_ENEMIES[location])
    enemy_level = random.randint(*LOCATION_LEVEL_RANGES[location])
    enemy = create_enemy(enemy_id, enemy_level, rarity)

    if battle(player, enemy, world, location):
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

        enemy = create_enemy(
            enemy_ids[enemy_index],
            world.get_optional_enemy_level(location, enemy_index),
            world.get_optional_enemy_rarity(location, enemy_index),
        )
        if battle(player, enemy, world, location):
            world.defeat_optional_enemy(location, enemy_index)
        else:
            return


def claim_location_chest(player, location, world, rng=None):
    if not world.is_chest_available(location):
        return None

    reward = generate_chest_reward(
        LOCATION_LEVEL_RANGES[location],
        rng,
    )
    stored_in_inventory = player.inventory.add_item(reward["weapon"])
    if not stored_in_inventory and not world.add_ground_loot(
        location,
        reward["weapon"],
    ):
        return None
    if not world.open_chest(location):
        if stored_in_inventory:
            player.inventory.remove_item(reward["weapon"])
        else:
            world.take_ground_loot(location, reward["weapon"])
        return None

    player.gold += reward["gold"]
    reward["stored_in_location"] = not stored_in_inventory
    return reward
