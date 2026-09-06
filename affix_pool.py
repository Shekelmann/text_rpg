"""First playable test pool. Tier 1 is a version label, not a tier scale."""

from affix import (
    Affix, AffixType, Condition, ConditionType, Modifier, ModifierOperation,
    OnHitEffect, OnHitEffectType,
)


WEAPON_AFFIX_POOL = (
    Affix("sharpened", "Заточенный", AffixType.PREFIX, 1, (
        Modifier("physical_damage", ModifierOperation.FLAT, 4),
    ), "+4 базового физического урона"),
    Affix("heavy", "Тяжёлый", AffixType.PREFIX, 1, (
        Modifier("physical_damage", ModifierOperation.FLAT, 8),
        Modifier("dodge_chance", ModifierOperation.PERCENT, -40),
    ), "+8 базового физического урона; −40% уклонения"),
    Affix("light", "Лёгкий", AffixType.PREFIX, 1, (
        Modifier("physical_damage", ModifierOperation.FLAT, -2),
        Modifier("dodge_chance", ModifierOperation.PERCENT, 30),
    ), "−2 базового физического урона; +30% уклонения"),
    Affix("poisonous", "Ядовитый", AffixType.PREFIX, 1, (),
          "При попадании накладывает 2 Poison (яд)",
          (OnHitEffect(OnHitEffectType.POISON, 2),)),
    Affix("serrated", "Зазубренный", AffixType.PREFIX, 1, (),
          "При попадании накладывает Bleeding: 2 урона за следующие 2 атакующих действия цели",
          (OnHitEffect(OnHitEffectType.BLEEDING, 2, 2),)),
    Affix("assassin", "Убийцы", AffixType.SUFFIX, 1, (
        Modifier("physical_damage", ModifierOperation.PERCENT, 15,
                 Condition(ConditionType.TARGET_HP_BELOW, 0.20)),
    ), "+15% базового физического урона, если у цели меньше 20% HP"),
    Affix("berserker", "Берсерка", AffixType.SUFFIX, 1, (
        Modifier("attack_physical_damage", ModifierOperation.PERCENT, 20,
                 Condition(ConditionType.SOURCE_HP_BELOW, 0.30)),
    ), "+20% физического урона атаки, если у игрока меньше 30% HP"),
    Affix("bloodletter", "Кровопускателя", AffixType.SUFFIX, 1, (
        Modifier("physical_damage", ModifierOperation.PERCENT, 20,
                 Condition(ConditionType.TARGET_BLEEDING)),
    ), "+20% базового физического урона по целям с кровотечением"),
    Affix("poisoner", "Отравителя", AffixType.SUFFIX, 1, (
        Modifier("physical_damage", ModifierOperation.PERCENT, 20,
                 Condition(ConditionType.TARGET_POISONED)),
    ), "+20% базового физического урона по отравленным целям"),
    Affix("duelist", "Дуэлянта", AffixType.SUFFIX, 1, (
        Modifier("crit_chance", ModifierOperation.FLAT, 0.10),
    ), "+10 процентных пунктов к шансу критического удара"),
)
