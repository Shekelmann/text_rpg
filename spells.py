"""Combat spell content registry used by new characters and the spellbook."""
from effects import PhysicalShield, Stun, Heal, GainActionPoint
from spell import Spell


SPELLS = {
    "healing": Spell(
        "healing", "Лечение",
        "Восстанавливает 20 HP, но не выше максимального здоровья.",
        cost=5, resource="mana", target="self", action_cost=1, effects=(Heal(20),),
    ),
    "slow_time": Spell(
        "slow_time", "Замедлить время",
        "Добавляет 1 ОД только в текущем ходу. Можно применить один раз за ход.",
        cost=10, resource="mana", target="self", action_cost=0,
        effects=(GainActionPoint(1),),
    ),
    "magic_shield": Spell(
        "magic_shield", "Магический щит",
        "До начала следующего хода уменьшает входящий физический урон на 30%.",
        cost=6, resource="mana", target="self", action_cost=1,
        effects=(PhysicalShield(0.30),),
    ),
    "stun": Spell(
        "stun", "Оглушение",
        "Выбранный противник пропускает свой следующий ход.",
        cost=5, resource="mana", action_cost=1,
        effects=(Stun(),),
    ),
}

_STARTING_SET = ("healing", "slow_time", "magic_shield", "stun")
STARTING_SPELL_IDS = {
    "bruiser": _STARTING_SET,
    "daredevil": _STARTING_SET,
    "herald": _STARTING_SET,
}


def grant_starting_spells(player, class_id):
    for spell_id in STARTING_SPELL_IDS.get(class_id, ()):
        player.learn_spell(SPELLS[spell_id])
