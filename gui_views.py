"""Read-only view models, built on the game thread and copied to the UI queue.

No domain objects cross into Tk callbacks. Calculated stats come from Player's
existing methods; this module only formats their results.
"""

from player import ARMOR_SLOTS
from item_presenter import item_icon_path, item_tooltip_rows

ACCESSORY_SLOTS = (("ring_1", "Кольцо I"), ("ring_2", "Кольцо II"),
                   ("amulet", "Амулет"), ("belt", "Пояс"))


def equipment_snapshot(player):
    slots = [(slot, SLOT_LABELS.get(slot, slot)) for slot in ("main_hand", "off_hand", *ARMOR_SLOTS)]
    result = []
    for slot, label in (*slots, *ACCESSORY_SLOTS):
        item = getattr(player, slot, None)
        path = item_icon_path(item) if item else None
        future = (slot, label) in ACCESSORY_SLOTS and not hasattr(player, slot)
        result.append(dict(id=slot, label=label, name=item.name if item else "—",
                           icon=str(path) if path else None, future=future,
                           tooltip=item_tooltip_rows(item) if item else (label, "Будущий слот аксессуара" if future else "Не экипировано")))
    return tuple(result)


def flask_snapshot(player):
    """Read actual charges, availability and catalog restoration amounts."""
    from objects import ITEMS
    state = getattr(player, "flasks", {})
    return tuple(dict(id=key, name=f"{key.upper()} Flask", resource=key.upper(),
                      count=getattr(state.get(key), "count", None),
                      amount=(getattr(state.get(key), "restore_amount", None)
                              or ITEMS[{"hp": "heal", "mp": "mana"}[key]].restore_amount),
                      usable=player.can_use_flask(key)) for key in ("hp", "mp"))


SLOT_LABELS = {
    "main_hand": "Основная рука", "off_hand": "Вторая рука",
    "head": "Голова", "body": "Тело", "legs": "Ноги",
    "hands": "Руки", "feet": "Ступни",
}


def character_snapshot(player):
    weapon = player.main_hand
    damage = "—"
    if weapon:
        minimum, maximum = player.get_attack_damage_range()
        damage = f"{minimum}–{maximum}"
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
        "equipment_slots": equipment_snapshot(player),
        "flasks": flask_snapshot(player),
        "spellbook": spellbook_snapshot(player),
    }


def spellbook_snapshot(player):
    from item_presenter import EFFECT_NAMES

    effect_names = {**EFFECT_NAMES, "regeneration": "Регенерация"}

    def entry(spell, count=None):
        effects = []
        for effect in spell.effects:
            name = effect_names.get(type(effect).__name__.lower(), type(effect).__name__)
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
                    details=f"{spell.name}\n\n{spell.description}\n\nСтоимость: {cost}\nЦель: {target}\nУрон: {damage}\nЭффекты: "
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
