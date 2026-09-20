"""Canonical weapon-specific affix pools used by loot and rerolls."""

from affix import (
    Affix, AffixType, Modifier, ModifierOperation, OnHitEffect,
    OnHitEffectType,
)


PHYSICAL_DAMAGE = Affix(
    "sharp", "Острый", AffixType.PREFIX, 1,
    (Modifier("physical_damage", ModifierOperation.FLAT, 4),),
    "+4 к базовому физическому урону оружия.",
)
POISON = Affix(
    "poisonous", "Ядовитый", AffixType.PREFIX, 1, (),
    "При попадании накладывает 2 Poison.",
    (OnHitEffect(OnHitEffectType.POISON, 2),),
)
BLEEDING = Affix(
    "serrated", "Зазубренный", AffixType.PREFIX, 1, (),
    "При попадании накладывает Bleeding: 2 урона за 2 атакующих действия цели.",
    (OnHitEffect(OnHitEffectType.BLEEDING, 2, 2),),
)
ARMOR_PENETRATION = Affix(
    "penetrating", "Пробивающий", AffixType.PREFIX, 1,
    (Modifier("armor_penetration", ModifierOperation.FLAT, 0.30),),
    "Текущий удар игнорирует 30% брони цели.",
)
ARMOR_BREAK = Affix(
    "armor_breaker", "Крушителя", AffixType.SUFFIX, 1, (),
    "При попадании снижает броню цели на 30% на 2 хода цели.",
    (OnHitEffect(OnHitEffectType.ARMOR_BREAK, 0.30, 2),),
)
ASTRAL_DAMAGE = Affix(
    "astral_power", "Астральный", AffixType.PREFIX, 1,
    (Modifier("astral_damage", ModifierOperation.FLAT, 4),),
    "+4 к базовому астральному урону оружия.",
)
ASTRAL_AMPLIFICATION = Affix(
    "astral_focus", "Сфокусированный", AffixType.SUFFIX, 1,
    (Modifier("astral_damage", ModifierOperation.PERCENT, 15),),
    "+15% к базовому астральному урону оружия.",
)


WEAPON_AFFIX_POOLS = {
    "dagger": (POISON, BLEEDING),
    "sword": (BLEEDING, PHYSICAL_DAMAGE),
    "axe": (BLEEDING, PHYSICAL_DAMAGE),
    "axe_2h": (ARMOR_PENETRATION, PHYSICAL_DAMAGE),
    "club": (ARMOR_BREAK, PHYSICAL_DAMAGE),
    "staff": (ASTRAL_DAMAGE, ASTRAL_AMPLIFICATION),
}

# Complete catalog for filters and old imports. Generation never uses it.
ALL_WEAPON_AFFIXES = tuple(dict.fromkeys(
    affix
    for pool in WEAPON_AFFIX_POOLS.values()
    for affix in pool
))
WEAPON_AFFIX_POOL = ALL_WEAPON_AFFIXES


def get_weapon_affix_pool(weapon_or_id):
    weapon_id = (
        weapon_or_id if isinstance(weapon_or_id, str)
        else getattr(weapon_or_id, "icon_id", None)
    )
    try:
        return WEAPON_AFFIX_POOLS[weapon_id]
    except KeyError as error:
        raise ValueError(f"Unknown weapon affix pool: {weapon_id}") from error


def reroll_weapon_affixes(weapon, rng=None):
    """Shared generation entry point for loot and a future blacksmith UI."""
    return weapon.reroll_affixes(rng)
