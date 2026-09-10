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

TOOLTIP_COLORS = {
    "critical": "#f0a04b",
    "bleeding": "#ef6565",
    "poison": "#66c873",
    "astral": "#bd82e6",
    "drain": "#bd82e6",
}


def _row(*parts):
    return tuple((text, style) for text, style in parts if text)


def item_tooltip_rows(item):
    """Build semantic tooltip rows from existing item data.

    Each fragment is ``(text, style)``.  Keeping the style beside the domain
    value lets every GUI item container render the same tooltip without
    parsing the localized display text.
    """
    rows = [_row((getattr(item, "display_name", getattr(item, "name", "Предмет")), None))]
    rarity = getattr(item, "rarity", None)
    if rarity is not None and getattr(rarity, "title", None):
        rows.append(_row((f"Редкость: {rarity.title}", None)))

    item_type = getattr(item, "item_type", None)
    if item_type:
        rows.append(_row((f"Тип: {ITEM_TYPE_NAMES.get(item_type, item_type)}", None)))

    if getattr(item, "is_weapon", False):
        weapon_level = getattr(item, "level", 1)
        rows.append(_row((f"Уровень оружия: {weapon_level}", None)))
        rows.append(_row((f"Требуемый уровень персонажа: {weapon_level}", None)))
        damage_type = getattr(item, "damage_type", None)
        is_astral = getattr(damage_type, "name", None) == "ASTRAL"
        damage_style = "astral" if is_astral else None
        base = item.get_scaled_base_damage_range()
        final = (item.final_min_damage, item.final_max_damage)
        if final == base:
            rows.append(_row(("Урон: ", None), (f"{final[0]}–{final[1]}", damage_style)))
        else:
            rows.append(_row(("Базовый урон: ", None), (f"{base[0]}–{base[1]}", damage_style)))
            rows.append(_row(("Итоговый урон: ", None), (f"{final[0]}–{final[1]}", damage_style)))
        if damage_type is not None:
            damage_name = getattr(damage_type, "value", damage_type)
            rows.append(_row(("Тип урона: ", None), (str(damage_name), damage_style)))
        rows.append(_row(
            ("Критический удар", "critical"),
            (": ", None),
            (f"{item.final_crit_chance:.0%}", "critical"),
        ))
        if getattr(item, "weapon_type", None):
            rows.append(_row((f"Хват: {item.weapon_type}", None)))
        rows.append(_row((f"Стоимость: {item.price} золота", None)))

    if getattr(item, "item_type", None) == "armor" and hasattr(item, "defense"):
        rows.append(_row((f"Броня: {item.defense}", None)))
    if hasattr(item, "heal"):
        rows.append(_row((f"Восстанавливает HP: {item.heal}", None)))

    for affix in getattr(item, "affixes", ()):
        description = getattr(affix, "description", "")
        rows.append(_row((f"{affix.name}: {description}" if description else affix.name, None)))
        for effect in getattr(affix, "effects", ()):
            effect_id = getattr(getattr(effect, "type", None), "value", None)
            effect_name = EFFECT_NAMES.get(effect_id, str(effect_id or "Эффект"))
            style = effect_id if effect_id in TOOLTIP_COLORS else None
            parameters = str(effect.value)
            if getattr(effect, "triggers", 0):
                parameters += f", {effect.triggers} срабатывания"
            rows.append(_row(
                (effect_name, style),
                (": ", None),
                (parameters, style),
            ))

    return tuple(row for row in rows if row)


def item_icon_path(item):
    """Return prepared artwork when one exists; unknown items are safe."""
    if not getattr(item, "is_weapon", False):
        return None
    return weapon_icon_path(item)


def item_tooltip_lines(item):
    """Return plain text for non-rich clients and existing callers."""
    return tuple("".join(text for text, _style in row) for row in item_tooltip_rows(item))
