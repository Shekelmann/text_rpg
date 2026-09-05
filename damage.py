from enum import Enum
import math

class Damage_type(Enum):
	PHYSICAL = "Физический урон"
	ELEMENTAL = "Элементальный урон"
	ASTRAL = "Астральный урон"
	MAGICAL = "Астральный урон"


RESISTANCE_CAP = 0.70
RESISTIBLE_DAMAGE_TYPES = frozenset({
	Damage_type.ASTRAL,
	Damage_type.ELEMENTAL,
})


def reduce_damage_by_resistance(damage, resistance):
	resistance = min(RESISTANCE_CAP, max(0, resistance))
	remaining_damage = round(damage * (1 - resistance), 10)
	return math.ceil(remaining_damage)
