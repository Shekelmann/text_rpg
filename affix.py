"""Data-only affixes and a pool-driven generator; no tier balancing."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from math import isfinite

from rarity import Rarity
from effects import Poison, Bleeding


class ConditionType(Enum):
    TARGET_HP_BELOW = "target_hp_below"
    SOURCE_HP_BELOW = "source_hp_below"
    TARGET_POISONED = "target_poisoned"
    TARGET_BLEEDING = "target_bleeding"


@dataclass(frozen=True)
class Condition:
    type: ConditionType
    threshold: float = 0

    def matches(self, source=None, target=None):
        if self.type in (ConditionType.TARGET_HP_BELOW, ConditionType.SOURCE_HP_BELOW):
            actor = source if self.type == ConditionType.SOURCE_HP_BELOW else target
            return (actor is not None and actor.max_health > 0
                    and actor.health < actor.max_health * self.threshold)
        if target is None:
            return False
        effect_type = {
            ConditionType.TARGET_POISONED: Poison,
            ConditionType.TARGET_BLEEDING: Bleeding,
        }[self.type]
        return any(isinstance(effect, effect_type) and not effect.is_expired
                   for effect in target.effects.effects)


class OnHitEffectType(Enum):
    POISON = "poison"
    BLEEDING = "bleeding"


@dataclass(frozen=True)
class OnHitEffect:
    type: OnHitEffectType
    value: int
    triggers: int = 0

    def create(self):
        # Each hit gets a fresh mutable status; definitions can be shared safely.
        if self.type == OnHitEffectType.POISON:
            return Poison(self.value)
        if self.type == OnHitEffectType.BLEEDING:
            return Bleeding(self.value, self.triggers)
        raise ValueError("Unsupported on-hit effect")


class AffixType(Enum):
    PREFIX = "prefix"
    SUFFIX = "suffix"


class ModifierOperation(Enum):
    FLAT = "flat"
    PERCENT = "percent"


@dataclass(frozen=True)
class Modifier:
    target: str
    operation: ModifierOperation
    value: float
    condition: Condition | None = None

    def __post_init__(self):
        if not self.target or not isinstance(self.operation, ModifierOperation):
            raise ValueError("Modifier requires a target and a supported operation")
        if not isfinite(self.value):
            raise ValueError("Modifier value must be finite")


@dataclass(frozen=True)
class Affix:
    id: str
    name: str
    type: AffixType
    tier: int
    modifiers: tuple[Modifier, ...]
    description: str = ""
    effects: tuple[OnHitEffect, ...] = ()

    def __post_init__(self):
        if not self.id or not isinstance(self.type, AffixType):
            raise ValueError("Affix requires an id and a supported type")
        if type(self.tier) is not int or self.tier < 1:
            raise ValueError("Tier must be a positive integer")
        object.__setattr__(self, "modifiers", tuple(self.modifiers))
        object.__setattr__(self, "effects", tuple(self.effects))
        if any(not isinstance(effect, OnHitEffect) for effect in self.effects):
            raise TypeError("Expected OnHitEffect instances")
        if any(not isinstance(modifier, Modifier) for modifier in self.modifiers):
            raise TypeError("Expected Modifier instances")


AFFIX_COUNTS = {
    Rarity.COMMON: (0, 1),
    Rarity.RARE: (1, 2),
    Rarity.EPIC: (3, 4),
}
MAX_PER_TYPE = 2


def validate_affixes(affixes):
    if any(not isinstance(affix, Affix) for affix in affixes):
        raise TypeError("Expected Affix instances")
    if len({affix.id for affix in affixes}) != len(affixes):
        raise ValueError("Duplicate affix ids on an item")
    for affix_type in AffixType:
        if sum(affix.type == affix_type for affix in affixes) > MAX_PER_TYPE:
            raise ValueError("At most two affixes of each type are allowed")


def apply_modifiers(base, target, modifiers, source=None, defender=None):
    """Percent values use 10 for +10%; all flats precede summed percents."""
    flat = percent = 0
    for modifier in modifiers:
        if modifier.target != target:
            continue
        if modifier.condition is not None and not modifier.condition.matches(source, defender):
            continue
        if modifier.operation == ModifierOperation.FLAT:
            flat += modifier.value
        elif modifier.operation == ModifierOperation.PERCENT:
            percent += modifier.value
    return (base + flat) * (1 + percent / 100)


def generate_affixes(rarity, pool, rng=None):
    """Choose versions as supplied, without replacement or tier scaling.

    An insufficient pool raises rather than silently lowering the rolled count.
    IDs identify versions and must be unique within the supplied pool.
    """
    if rarity not in AFFIX_COUNTS:
        raise ValueError("Affix generation is not implemented for this rarity")
    rng = random if rng is None else rng
    pool = tuple(pool)
    if any(not isinstance(affix, Affix) for affix in pool):
        raise TypeError("Expected Affix instances")
    if len({affix.id for affix in pool}) != len(pool):
        raise ValueError("Pool contains duplicate affix ids")
    count = rng.randint(*AFFIX_COUNTS[rarity])
    available = {kind: [a for a in pool if a.type == kind] for kind in AffixType}
    if sum(min(MAX_PER_TYPE, len(group)) for group in available.values()) < count:
        raise ValueError("Insufficient affix pool for the rolled count")
    selected = []
    counts = {kind: 0 for kind in AffixType}
    for _ in range(count):
        kind = rng.choice([kind for kind in AffixType
                           if available[kind] and counts[kind] < MAX_PER_TYPE])
        affix = rng.choice(available[kind])
        available[kind].remove(affix)
        counts[kind] += 1
        selected.append(affix)
    return tuple(selected)
