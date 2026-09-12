"""Spell definitions and ownership, independent of UI, classes and turn policy."""
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional, Tuple

from damage import Damage_type
from effects import StatusEffect


@dataclass(frozen=True)
class CastResult:
    success: bool
    reason: str = ""
    damage: int = 0
    messages: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Spell:
    id: str
    name: str
    description: str = ""
    cost: int = 0
    resource: Optional[str] = None
    damage: int = 0
    damage_type: Optional[Damage_type] = None
    effects: Tuple[StatusEffect, ...] = ()
    target: str = "enemy"

    def __post_init__(self):
        if not self.id or not self.name:
            raise ValueError("Spell needs an ID and name")
        if type(self.cost) is not int or self.cost < 0 or type(self.damage) is not int or self.damage < 0:
            raise ValueError("Cost and damage must be nonnegative integers")
        if self.resource not in (None, "mana") or (self.cost and self.resource is None):
            raise ValueError("Only free spells and the existing mana resource are supported")
        if self.damage and not isinstance(self.damage_type, Damage_type):
            raise ValueError("Damage requires an explicit existing Damage_type")
        if any(not isinstance(effect, StatusEffect) for effect in self.effects):
            raise ValueError("Effects must use the existing StatusEffect system")
        if self.target not in ("enemy", "self"):
            raise ValueError("Spell target must be enemy or self")
        object.__setattr__(self, "effects", tuple(self.effects))

    def resolve_target(self, caster, target):
        return caster if self.target == "self" else target

    def check(self, caster, target):
        """Override alongside apply for a new mechanic; must not mutate state."""
        if not self.damage and not self.effects:
            return "Механика заклинания ещё не задана."
        target = self.resolve_target(caster, target)
        if target is None or not target.is_alive():
            return "Нет подходящей живой цели."
        return ""

    def apply(self, caster, target):
        """Called after check. Reuse mitigation and effects; no invented INT scaling.

        Extensions must return failure before changing state. Costs and ownership
        are handled by SpellBook.cast, never by this method or a UI callback.
        """
        target = self.resolve_target(caster, target)
        effects = deepcopy(self.effects)
        amount = self.damage
        if amount and hasattr(caster, "get_direct_damage_bonus"):
            amount += caster.get_direct_damage_bonus(self.damage_type)
        damage = target.take_damage(amount, self.damage_type) if amount else 0
        for effect in effects:
            if hasattr(effect, "source"):
                effect.source = caster
            target.add_effect(effect)
        messages = [f"Вы применяете «{self.name}»."]
        if damage:
            messages.append(f"Противник «{target.name}» получает {damage} урона.")
        for effect in effects:
            effect_name = getattr(effect, "display_name", type(effect).__name__)
            if self.target == "self":
                messages.append(f"На вас действует эффект «{effect_name}».")
            else:
                messages.append(
                    f"На противника «{target.name}» наложен эффект «{effect_name}»."
                )
        return CastResult(True, damage=damage, messages=tuple(messages))


class SpellBook:
    def __init__(self):
        self._definitions = {}
        self._learned = set()
        self._scrolls = {}

    def _register(self, spell):
        previous = self._definitions.get(spell.id)
        if previous is not None and previous != spell:
            raise ValueError(f"Conflicting spell definition: {spell.id}")
        self._definitions[spell.id] = spell

    def learn(self, spell):
        self._register(spell)
        if spell.id in self._learned:
            return False
        self._learned.add(spell.id)
        return True

    def add_scroll(self, spell, count=1):
        if type(count) is not int or count <= 0:
            raise ValueError("Scroll count must be a positive integer")
        self._register(spell)
        self._scrolls[spell.id] = self._scrolls.get(spell.id, 0) + count

    @property
    def learned(self):
        return tuple(self._definitions[key] for key in sorted(self._learned))

    @property
    def scrolls(self):
        return tuple((self._definitions[key], count) for key, count in sorted(self._scrolls.items()))

    def check(self, caster, spell_id, target=None, *, one_shot=False):
        owned = self._scrolls.get(spell_id, 0) > 0 if one_shot else spell_id in self._learned
        if not owned:
            return "Нет такого свитка." if one_shot else "Заклинание не изучено."
        spell = self._definitions[spell_id]
        if not caster.is_alive():
            return "Персонаж не может применять заклинания."
        if spell.resource == "mana" and caster.mana < spell.cost:
            return "Недостаточно MP."
        return spell.check(caster, target)

    def cast(self, caster, spell_id, target=None, *, one_shot=False):
        reason = self.check(caster, spell_id, target, one_shot=one_shot)
        if reason:
            return CastResult(False, reason)
        spell = self._definitions[spell_id]
        result = spell.apply(caster, target)
        if not result.success:
            return result
        if spell.resource == "mana":
            caster.mana -= spell.cost
        if one_shot:
            self._scrolls[spell_id] -= 1
            if not self._scrolls[spell_id]:
                del self._scrolls[spell_id]
        return result
