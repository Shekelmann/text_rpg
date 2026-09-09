from dataclasses import dataclass, field

from damage import Damage_type


@dataclass(frozen=True)
class CombatAction:
    name: str
    is_attack: bool = False


ATTACK_ACTION = CombatAction("attack", is_attack=True)
NON_ATTACK_ACTION = CombatAction("non_attack")


@dataclass
class EffectResult:
    damage: int = 0
    health_restored: int = 0
    mana_restored: int = 0
    messages: list = field(default_factory=list)

    def include(self, other):
        self.damage += other.damage
        self.health_restored += other.health_restored
        self.mana_restored += other.mana_restored
        self.messages.extend(other.messages)


def _deal_effect_damage(target, damage, damage_type=None):
    return target.take_damage(
        damage,
        damage_type,
        bypass_mitigation=damage_type is None,
    )


def _effect_target_text(target):
    if getattr(target, "is_player", False):
        return "вам"
    return f"противнику «{target.name}»"


class StatusEffect:
    stack_key = None

    @property
    def is_expired(self):
        return False

    def stack(self, other):
        return False

    def on_turn_start(self, target):
        return EffectResult()

    def on_action_performed(self, target, action):
        return EffectResult()


class Poison(StatusEffect):
    def __init__(self, value, damage_type=None):
        self.value = value
        self.damage_type = damage_type

    @property
    def stack_key(self):
        if self.damage_type is None:
            return "poison"
        return ("poison", self.damage_type)

    @property
    def is_expired(self):
        return self.value <= 0

    def stack(self, other):
        self.value += other.value
        return True

    def on_turn_start(self, target):
        if self.is_expired:
            return EffectResult()

        damage = _deal_effect_damage(
            target,
            self.value,
            self.damage_type,
        )
        self.value -= 1
        return EffectResult(
            damage=damage,
            messages=[
                f"Яд наносит {_effect_target_text(target)} {damage} урона."
            ],
        )


class Bleeding(StatusEffect):
    def __init__(self, damage, triggers, damage_type=None):
        self.damage = damage
        self.triggers = triggers
        self.damage_type = damage_type

    @property
    def is_expired(self):
        return self.triggers <= 0

    def on_action_performed(self, target, action):
        if self.is_expired or not action.is_attack:
            return EffectResult()

        damage = _deal_effect_damage(
            target,
            self.damage,
            self.damage_type,
        )
        self.triggers -= 1
        return EffectResult(
            damage=damage,
            messages=[
                f"Кровотечение наносит "
                f"{_effect_target_text(target)} {damage} урона."
            ],
        )


class Drain(StatusEffect):
    def __init__(self, value, source=None):
        self.value = value
        self.source = source
        self.damage_type = Damage_type.ASTRAL
        self.ticks_remaining = 2

    @property
    def stack_key(self):
        return "drain"

    @property
    def is_expired(self):
        return self.ticks_remaining <= 0

    def stack(self, other):
        # An active Drain keeps its damage, source and remaining duration.
        return True

    def on_turn_start(self, target):
        if self.is_expired or self.source is None:
            return EffectResult()
        return self.trigger(target)

    def trigger(self, target, source=None):
        if self.is_expired:
            return EffectResult()
        if source is not None:
            self.source = source
        if self.source is None:
            return EffectResult()

        damage = _deal_effect_damage(
            target,
            self.value,
            self.damage_type,
        )
        restore = damage // 2

        old_health = self.source.health
        old_mana = self.source.mana
        self.source.health = min(
            self.source.max_health,
            self.source.health + restore,
        )
        self.source.mana = min(
            self.source.max_mana,
            self.source.mana + restore,
        )
        self.ticks_remaining -= 1

        health_restored = self.source.health - old_health
        mana_restored = self.source.mana - old_mana
        return EffectResult(
            damage=damage,
            health_restored=health_restored,
            mana_restored=mana_restored,
            messages=[
                f"Иссушение наносит {_effect_target_text(target)} "
                f"{damage} урона и восстанавливает "
                f"{health_restored} HP, {mana_restored} MP."
            ],
        )


class EffectCollection:
    def __init__(self):
        self.effects = []

    def add(self, effect):
        if effect.stack_key is not None:
            existing = self.get_by_stack_key(effect.stack_key)
            if existing is not None:
                existing.stack(effect)
                return existing
        self.effects.append(effect)
        return effect

    def get_by_stack_key(self, stack_key):
        return next(
            (
                effect
                for effect in self.effects
                if effect.stack_key == stack_key
            ),
            None,
        )

    def contains(self, effect_type):
        return any(isinstance(effect, effect_type) for effect in self.effects)

    def _remove_expired(self):
        self.effects = [
            effect for effect in self.effects
            if not effect.is_expired
        ]

    def on_turn_start(self, target):
        result = EffectResult()
        for effect in list(self.effects):
            result.include(effect.on_turn_start(target))
        self._remove_expired()
        return result

    def on_action_performed(self, target, action):
        result = EffectResult()
        for effect in list(self.effects):
            result.include(effect.on_action_performed(target, action))
        self._remove_expired()
        return result
