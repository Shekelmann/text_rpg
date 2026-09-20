"""Read-only view models, built on the game thread and copied to the UI queue.

No domain objects cross into Tk callbacks. Calculated stats come from Player's
existing methods; this module only formats their results.
"""

from player import ACCESSORY_SLOTS as PLAYER_ACCESSORY_SLOTS, ARMOR_SLOTS
from item_presenter import item_icon_path, item_tooltip_rows
from intent import intent_presentation

ACCESSORY_LABELS = {
    "ring_1": "Кольцо I", "ring_2": "Кольцо II",
    "amulet": "Амулет", "belt": "Пояс",
}


def equipment_snapshot(player):
    slots = [(slot, SLOT_LABELS.get(slot, slot)) for slot in ("main_hand", "off_hand", *ARMOR_SLOTS)]
    result = []
    accessory_slots = tuple((slot, ACCESSORY_LABELS[slot]) for slot in PLAYER_ACCESSORY_SLOTS)
    for slot, label in (*slots, *accessory_slots):
        item = getattr(player, slot, None)
        path = item_icon_path(item) if item else None
        future = not hasattr(player, slot)
        removable = item is not None and not (
            slot == "off_hand" and item is getattr(player, "main_hand", None)
        )
        result.append(dict(id=slot, label=label, name=item.name if item else "—",
                           icon=str(path) if path else None, future=future,
                           removable=removable,
                           tooltip=item_tooltip_rows(item) if item else (label, "Будущий слот аксессуара" if future else "Не экипировано")))
    return tuple(result)


def flask_snapshot(player):
    """Read permanent current/max flask charges and restoration amounts."""
    from flasks import HP_FLASK_RESTORE, MP_FLASK_RESTORE
    amounts = {"hp": HP_FLASK_RESTORE, "mp": MP_FLASK_RESTORE}
    return tuple(dict(id=key, name=f"{key.upper()} Flask", resource=key.upper(),
                      count=player.get_flask_count(key),
                      maximum=player.get_max_flask_count(key),
                      amount=amounts[key],
                      usable=player.can_use_flask(key)) for key in ("hp", "mp"))


SLOT_LABELS = {
    "main_hand": "Основная рука", "off_hand": "Вторая рука",
    "armor": "Доспех",
}


def character_snapshot(player, world=None):
    weapon = player.main_hand
    damage = "—"
    if weapon:
        ranges = (player.get_attack_damage_range(weapon=item) for item in player.attack_weapons())
        damage = " + ".join(f"{minimum}–{maximum}" for minimum, maximum in ranges)
    equipment = tuple(
        (SLOT_LABELS.get(slot, slot),
         getattr(item, "display_name", item.name) if item else "—")
        for slot in ("main_hand", "off_hand", *ARMOR_SLOTS)
        for item in (getattr(player, slot, None),)
    )
    hands = []
    for slot in ("main_hand", "off_hand"):
        item = getattr(player, slot, None)
        if item is None or (slot == "off_hand" and item is player.main_hand):
            continue
        hands.append({
            "id": slot,
            "label": SLOT_LABELS[slot],
            "name": getattr(item, "display_name", item.name),
            "tooltip": item_tooltip_rows(item),
        })
    return {
        "name": player.name,
        "day": getattr(world, "day", 1),
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
        "hands": tuple(hands),
        "effects": effects_snapshot(player),
        "equipment_slots": equipment_snapshot(player),
        "flasks": flask_snapshot(player),
        "abilities": ability_snapshot(player),
        "spellbook": spellbook_snapshot(player),
    }


EFFECT_ICONS = {
    "poison": "P", "bleeding": "Кр", "skip_turn": "Z",
    "magic_shield": "S", "fortify": "У", "drain": "И", "regeneration": "+",
}


def ability_snapshot(player):
    from ability import ABILITIES

    entries = {}
    for ability in player.abilities.unlocked:
        reason = player.abilities.check(player, ability.id)
        remaining = player.abilities.cooldown_remaining(ability.id)
        entries[ability.id] = {
            "id": ability.id,
            "name": ability.name,
            "description": ability.description,
            "class_requirement": ability.class_requirement,
            "action_point_cost": ability.action_point_cost,
            "cooldown": ability.cooldown,
            "cooldown_remaining": remaining,
            "equipped": player.abilities.is_equipped(ability.id),
            "usable": not reason,
            "reason": reason,
            "icon": ability.icon,
        }
    slots = tuple(
        entries.get(ability_id) if ability_id in ABILITIES else None
        for ability_id in player.abilities.slots
    )
    return {
        "available": tuple(entries[ability.id] for ability in player.abilities.unlocked),
        "slots": slots,
    }


def effects_snapshot(actor):
    """Same presentation contract for any actor, independent of intent."""
    return tuple({
        "id": effect.id,
        "effect_type": effect.effect_type.value,
        "icon": EFFECT_ICONS.get(effect.id, effect.display_name[:1]),
        "tooltip": effect.tooltip(),
    } for effect in actor.effects.active)


def enemy_effects_snapshot(enemy):
    return effects_snapshot(enemy)


def enemy_combat_snapshot(enemy):
    return {
        "enemy_name": enemy.name,
        "enemy_level": enemy.level,
        "enemy_health": enemy.health,
        "enemy_max_health": enemy.max_health,
        "enemy_image_id": getattr(enemy, "id", None),
        "enemy_intent": intent_presentation(enemy.intent),
        "enemy_effects": enemy_effects_snapshot(enemy),
    }


def spellbook_snapshot(player):
    from item_presenter import EFFECT_NAMES

    effect_names = {**EFFECT_NAMES, "regeneration": "Регенерация"}

    def entry(spell, count=None):
        effects = []
        for effect in spell.resolved_effects:
            name = getattr(effect, "display_name", effect_names.get(type(effect).__name__.lower(), type(effect).__name__))
            parameters = []
            for key, label in (("value", "сила"), ("damage", "урон"), ("triggers", "срабатывания"),
                               ("ticks_remaining", "оставшиеся срабатывания")):
                if hasattr(effect, key):
                    parameters.append(f"{label}: {getattr(effect, key)}")
            effects.append(name + (" (" + ", ".join(parameters) + ")" if parameters else ""))
        cost = f"{spell.cost} MP" if spell.resource == "mana" else "Без затрат ресурса"
        damage = (f"{spell.damage} + INT" if spell.damage else "Нет")
        damage += f" · {spell.damage_type.value}" if spell.damage_type else ""
        target = "Игрок" if spell.target == "self" else "Противник"
        return dict(id=spell.id, name=spell.name, count=count,
                    details=f"{spell.name}\n\n{spell.description}\n\nСтоимость: {spell.action_cost} ОД, {cost}\nЦель: {target}\nУрон: {damage}\nЭффекты: "
                            + ("; ".join(effects) or "Нет"))

    return {"learned": tuple(entry(spell) for spell in player.spellbook.learned),
            "scrolls": tuple(entry(spell, count) for spell, count in player.spellbook.scrolls)}


def map_snapshot(world, player):
    return tuple(
        (location_id == player.current_location, location["name"],
         tuple(world.locations[path]["name"] for path in location["paths"]),
         world.get_unavailable_message(location_id))
        for location_id, location in world.locations.items()
    )
