"""Read-only item presentation shared by graphical item containers."""

from weapon_icons import weapon_icon_path


ITEM_TYPE_NAMES = {
    "weapon": "Оружие",
    "armor": "Броня",
    "potion": "Расходник",
    "material": "Материал",
}

EFFECT_NAMES = {
    "poison": "Яд",
    "bleeding": "Кровотечение",
    "drain": "Иссушение",
}


def item_icon_path(item):
    """Return prepared artwork when one exists; unknown items are safe."""
    if not getattr(item, "is_weapon", False):
        return None
    return weapon_icon_path(item)


def item_tooltip_lines(item):
    """Build applicable tooltip rows directly from the item instance."""
    lines = [getattr(item, "display_name", getattr(item, "name", "Предмет"))]
    rarity = getattr(item, "rarity", None)
    if rarity is not None and getattr(rarity, "title", None):
        lines.append(f"Редкость: {rarity.title}")

    item_type = getattr(item, "item_type", None)
    if item_type:
        lines.append(f"Тип: {ITEM_TYPE_NAMES.get(item_type, item_type)}")

    if getattr(item, "is_weapon", False):
        base = (item.min_damage, item.max_damage)
        final = (item.final_min_damage, item.final_max_damage)
        if final == base:
            lines.append(f"Урон: {final[0]}–{final[1]}")
        else:
            lines.append(f"Базовый урон: {base[0]}–{base[1]}")
            lines.append(f"Итоговый урон: {final[0]}–{final[1]}")
        damage_type = getattr(item, "damage_type", None)
        if damage_type is not None:
            lines.append(f"Тип урона: {getattr(damage_type, 'value', damage_type)}")
        lines.append(f"Критический удар: {item.final_crit_chance:.0%}")
        if getattr(item, "weapon_type", None):
            lines.append(f"Хват: {item.weapon_type}")

    if getattr(item, "item_type", None) == "armor" and hasattr(item, "defense"):
        lines.append(f"Броня: {item.defense}")
    if hasattr(item, "heal"):
        lines.append(f"Восстанавливает HP: {item.heal}")

    for affix in getattr(item, "affixes", ()):
        description = getattr(affix, "description", "")
        lines.append(
            f"{affix.name}: {description}" if description else affix.name
        )
        for effect in getattr(affix, "effects", ()):
            effect_name = EFFECT_NAMES.get(
                getattr(getattr(effect, "type", None), "value", None),
                str(getattr(getattr(effect, "type", None), "value", "Эффект")),
            )
            parameters = [str(effect.value)]
            if getattr(effect, "triggers", 0):
                parameters.append(f"{effect.triggers} срабатывания")
            lines.append(f"{effect_name}: {', '.join(parameters)}")

    return tuple(line for line in lines if line)
