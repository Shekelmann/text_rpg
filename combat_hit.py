"""Resolve one direct weapon hit for either side of combat."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class HitResult:
    hit: bool
    damage: int = 0
    critical: bool = False
    rolled_damage: int = 0


def resolve_hit(
    target,
    roll_attack,
    damage_type,
    on_hit=None,
    rng=None,
    armor_penetration=0,
):
    """Dodge -> damage/crit roll -> mitigation -> on-hit, exactly once.

    A missed attack remains an attacking action; its action effects belong to
    the caller. Spells and DoT keep their existing, separate resolution rules.
    """
    rng = random if rng is None else rng
    dodge = target.get_dodge_chance()
    if dodge > 0 and rng.random() < dodge:
        return HitResult(False)
    damage, critical = roll_attack()
    if armor_penetration:
        received = target.take_damage(
            damage,
            damage_type,
            armor_penetration=armor_penetration,
        )
    else:
        received = target.take_damage(damage, damage_type)
    if on_hit is not None:
        on_hit(target)
    return HitResult(True, received, critical, damage)
