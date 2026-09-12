"""Small spell content registry used by new characters and the spellbook."""
from damage import Damage_type
from effects import Poison, Regeneration
from spell import Spell


SPELLS = {
    "astral_spark": Spell(
        "astral_spark", "Астральная искра",
        "Наносит противнику прямой астральный урон.",
        cost=3, resource="mana", damage=8,
        damage_type=Damage_type.ASTRAL,
    ),
    "venom_mark": Spell(
        "venom_mark", "Ядовитая метка",
        "Накладывает на противника ослабевающий яд.",
        cost=2, resource="mana",
        effects=(Poison(3, Damage_type.ASTRAL),),
    ),
    "renewal": Spell(
        "renewal", "Обновление",
        "Накладывает на героя регенерацию на два хода.",
        cost=3, resource="mana", target="self",
        effects=(Regeneration(4, ticks=2),),
    ),
}

_TEST_SET = ("astral_spark", "venom_mark", "renewal")
STARTING_SPELL_IDS = {
    "bruiser": _TEST_SET,
    "daredevil": _TEST_SET,
    "herald": _TEST_SET,
}


def grant_starting_spells(player, class_id):
    for spell_id in STARTING_SPELL_IDS.get(class_id, ()):
        player.learn_spell(SPELLS[spell_id])
