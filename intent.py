from enum import Enum


class EnemyIntent(str, Enum):
    """Broad category of the action an enemy plans to perform next."""

    PHYSICAL_ATTACK = "physical_attack"
    ASTRAL_ATTACK = "astral_attack"
    BUFF = "buff"
    DEBUFF = "debuff"


INTENT_PRESENTATION = {
    EnemyIntent.PHYSICAL_ATTACK: {
        "title": "Физическая атака",
        "description": "Враг собирается совершить физическую атаку.",
        "icon": "⚔",
    },
    EnemyIntent.ASTRAL_ATTACK: {
        "title": "Астральная атака",
        "description": "Враг собирается совершить астральную атаку.",
        "icon": "✦",
    },
    EnemyIntent.BUFF: {
        "title": "Бафф",
        "description": "Враг собирается усилить себя или союзника.",
        "icon": "▲",
    },
    EnemyIntent.DEBUFF: {
        "title": "Дебафф",
        "description": "Враг собирается наложить отрицательный эффект.",
        "icon": "▼",
    },
}


def intent_presentation(intent):
    """Return UI metadata while tolerating future serialized string values."""
    if not isinstance(intent, EnemyIntent):
        try:
            intent = EnemyIntent(intent)
        except (TypeError, ValueError):
            intent = EnemyIntent.PHYSICAL_ATTACK
    return dict(INTENT_PRESENTATION[intent], id=intent.value)
