"""Read-only view models, built on the game thread and copied to the UI queue.

No domain objects cross into Tk callbacks. Calculated stats come from Player's
existing methods; this module only formats their results.
"""

from player import ARMOR_SLOTS


SLOT_LABELS = {
    "main_hand": "Основная рука", "off_hand": "Вторая рука",
    "head": "Голова", "body": "Тело", "legs": "Ноги",
    "hands": "Руки", "feet": "Ступни",
}


def character_snapshot(player):
    weapon = player.main_hand
    damage = "—"
    if weapon:
        bonus = player.get_direct_damage_bonus(weapon.damage_type)
        damage = f"{weapon.final_min_damage + bonus}–{weapon.final_max_damage + bonus}"
    equipment = tuple(
        (SLOT_LABELS.get(slot, slot),
         getattr(item, "display_name", item.name) if item else "—")
        for slot in ("main_hand", "off_hand", *ARMOR_SLOTS)
        for item in (getattr(player, slot, None),)
    )
    return {
        "name": player.name,
        "class": player.character_class.name if player.character_class else "Без класса",
        "health": player.health, "max_health": player.max_health,
        "mana": player.mana, "max_mana": player.max_mana,
        "level": player.level, "strength": player.strength,
        "dexterity": player.dexterity, "intelligence": player.intelligence,
        "armor": player.get_armor_defense(), "gold": player.gold,
        "exp": player.exp, "exp_to_level": player.exp_to_level,
        "unspent": player.unspent_stat_points, "damage": damage,
        "inventory": f"{len(player.inventory.items)} / {player.inventory.size}",
        "equipment": equipment,
    }


def map_snapshot(world, player):
    return tuple(
        (location_id == player.current_location, location["name"],
         tuple(world.locations[path]["name"] for path in location["paths"]),
         world.get_unavailable_message(location_id))
        for location_id, location in world.locations.items()
    )
