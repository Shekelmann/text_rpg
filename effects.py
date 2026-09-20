from dataclasses import dataclass, field
from enum import Enum

from damage import Damage_type
from combat_feedback import damage_change, feedback_message, healing_change


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
    skip_turn: bool = False
    action_points_gain: int = 0
    messages: list = field(default_factory=list)

    def include(self, other):
        self.action_points_gain += other.action_points_gain
        self.damage += other.damage
        self.health_restored += other.health_restored
        self.mana_restored += other.mana_restored
        self.skip_turn = self.skip_turn or other.skip_turn
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


class EffectType(str, Enum):
    BUFF = "buff"
    DEBUFF = "debuff"


class StatusEffect:
    """Shared effect contract; each effect owns its timing and stacking policy."""

    id = "effect"
    display_name = "Эффект"
    stack_key = None
    effect_type = EffectType.DEBUFF
    instant = False
    description = ""

    def apply(self, target):
        return EffectResult()

    def on_turn_end(self, target):
        return EffectResult()

    def tooltip(self):
        parameters = []
        for key, label in (("value", "Сила"), ("damage", "Урон"),
                           ("triggers", "Атакующих действий осталось"),
                           ("ticks_remaining", "Срабатываний осталось")):
            if hasattr(self, key):
                parameters.append(f"{label}: {getattr(self, key)}")
        return (self.display_name, self.description, *parameters)

    @property
    def is_expired(self):
        return False

    def stack(self, other):
        return False

    def on_turn_start(self, target):
        return EffectResult()

    def on_action_performed(self, target, action):
        return EffectResult()

    def modify_incoming_damage(self, damage, damage_type):
        return damage

    def modify_armor(self, armor):
        return armor

    def configure_for_source(self, source):
        """Resolve optional stat scaling on a copied effect definition."""
        return self


class Heal(StatusEffect):
    id = "heal"
    display_name = "Лечение"
    description = "Мгновенно восстанавливает HP, не выше максимума."
    effect_type = EffectType.BUFF
    instant = True

    def __init__(self, value, intelligence_scaling=0):
        if type(value) is not int or value < 0:
            raise ValueError("Healing must be a nonnegative integer")
        if type(intelligence_scaling) is not int or intelligence_scaling < 0:
            raise ValueError("Healing scaling must be a nonnegative integer")
        self.base_value = value
        self.value = value
        self.intelligence_scaling = intelligence_scaling

    def configure_for_source(self, source):
        self.value = (
            self.base_value
            + getattr(source, "intelligence", 0) * self.intelligence_scaling
        )
        return self

    def apply(self, target):
        old_health = target.health
        target.health = min(target.max_health, target.health + self.value)
        restored = target.health - old_health
        text = (f"Вы восстанавливаете {restored} HP." if getattr(target, "is_player", False)
                else f"{target.name} восстанавливает {restored} HP.")
        return EffectResult(health_restored=restored, messages=[feedback_message(
            text, healing_change(target, old_health, target.health),
        )])


class GainActionPoint(StatusEffect):
    id = "gain_action_point"
    display_name = "Дополнительное ОД"
    description = "Добавляет ОД только в текущем ходу."
    effect_type = EffectType.BUFF
    instant = True

    def __init__(self, value=1):
        if type(value) is not int or value < 0:
            raise ValueError("Action point gain must be a nonnegative integer")
        self.value = value

    def apply(self, target):
        # The turn controller consumes this result; no persistent actor stat.
        return EffectResult(action_points_gain=self.value, messages=[
            f"Вы получаете +{self.value} ОД в этом ходу." if getattr(target, "is_player", False)
            else f"{target.name} получает +{self.value} ОД в этом ходу.",
        ])


class PhysicalShield(StatusEffect):
    """Protects until the next turn of its owner."""

    id = "magic_shield"
    effect_type = EffectType.BUFF
    description = "Уменьшает физический урон на 30% до начала следующего хода. Не влияет на астральный урон."

    stack_key = "physical_shield"
    display_name = "Магический щит"

    def __init__(
        self,
        reduction=0.30,
        intelligence_scaling=0,
        maximum_reduction=0.60,
    ):
        if not 0 <= reduction <= 1:
            raise ValueError("Shield reduction must be between 0 and 1")
        if not 0 <= intelligence_scaling <= 1:
            raise ValueError("Shield scaling must be between 0 and 1")
        if not 0 <= maximum_reduction <= 1:
            raise ValueError("Shield maximum must be between 0 and 1")
        self.base_reduction = reduction
        self.intelligence_scaling = intelligence_scaling
        self.maximum_reduction = maximum_reduction
        self.reduction = reduction
        self.expires_at_turn_start = True

    def configure_for_source(self, source):
        self.reduction = min(
            self.maximum_reduction,
            self.base_reduction
            + getattr(source, "intelligence", 0) * self.intelligence_scaling,
        )
        return self

    @property
    def is_expired(self):
        return not self.expires_at_turn_start

    def stack(self, other):
        # Refresh, but never multiply or add equal shields.
        self.reduction = max(self.reduction, other.reduction)
        self.expires_at_turn_start = True
        return True

    def modify_incoming_damage(self, damage, damage_type):
        if damage_type == Damage_type.PHYSICAL and not self.is_expired:
            return damage * (1 - self.reduction)
        return damage

    def on_turn_start(self, target):
        self.expires_at_turn_start = False
        return EffectResult(messages=["Действие «Магического щита» заканчивается."])


class Fortify(StatusEffect):
    """Doubles current armor until the owner's next turn starts."""

    id = "fortify"
    display_name = "Укрепление"
    description = "Удваивает текущую броню до начала следующего хода."
    effect_type = EffectType.BUFF
    stack_key = "fortify"

    def __init__(self):
        self.expires_at_turn_start = True

    @property
    def is_expired(self):
        return not self.expires_at_turn_start

    def stack(self, other):
        self.expires_at_turn_start = True
        return True

    def modify_armor(self, armor):
        return armor * 2 if not self.is_expired else armor

    def on_turn_start(self, target):
        self.expires_at_turn_start = False
        return EffectResult(messages=["Действие «Укрепления» заканчивается."])


class ArmorBreak(StatusEffect):
    """Temporarily lowers the target's armor without changing its base value."""

    id = "armor_break"
    display_name = "Слом брони"
    description = "Временно снижает броню цели."
    effect_type = EffectType.DEBUFF
    stack_key = "armor_break"

    def __init__(self, reduction=0.30, turns_remaining=2):
        if not 0 <= reduction <= 1:
            raise ValueError("Armor reduction must be between 0 and 1")
        if type(turns_remaining) is not int or turns_remaining < 1:
            raise ValueError("Armor Break duration must be a positive integer")
        self.reduction = reduction
        self.turns_remaining = turns_remaining

    @property
    def is_expired(self):
        return self.turns_remaining <= 0

    def stack(self, other):
        # Reapplication refreshes one shared debuff; reductions never add up.
        self.reduction = max(self.reduction, other.reduction)
        self.turns_remaining = other.turns_remaining
        return True

    def modify_armor(self, armor):
        if self.is_expired:
            return armor
        return armor * (1 - self.reduction)

    def on_turn_start(self, target):
        self.turns_remaining -= 1
        if self.is_expired:
            return EffectResult(messages=["Действие «Слома брони» заканчивается."])
        return EffectResult()

    def tooltip(self):
        percent = round(self.reduction * 100)
        return (
            self.display_name,
            f"Броня снижена на {percent}% ещё {self.turns_remaining} ходов.",
        )


class Stun(StatusEffect):
    id = "skip_turn"
    effect_type = EffectType.DEBUFF
    description = "Пропускает следующий ход, затем снимается. Повторное наложение не добавляет пропусков."

    stack_key = "stun"
    display_name = "Оглушение"

    def __init__(self):
        self.pending = True

    @property
    def is_expired(self):
        return not self.pending

    def stack(self, other):
        self.pending = True
        return True

    def on_turn_start(self, target):
        if not self.pending:
            return EffectResult()
        self.pending = False
        return EffectResult(
            skip_turn=True,
            messages=[f"{target.name} оглушён и пропускает ход."],
        )


class Poison(StatusEffect):
    id = "poison"
    effect_type = EffectType.DEBUFF
    description = "Наносит урон в начале хода. После каждого срабатывания сила яда уменьшается на 1."

    display_name = "Яд"

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

        old_health = target.health
        damage = _deal_effect_damage(
            target,
            self.value,
            self.damage_type,
        )
        self.value -= 1
        return EffectResult(
            damage=damage,
            messages=[feedback_message(
                f"Яд наносит {_effect_target_text(target)} {damage} урона.",
                damage_change(target, old_health, target.health, self.damage_type),
            )],
        )


class Bleeding(StatusEffect):
    id = "bleeding"
    effect_type = EffectType.DEBUFF
    description = "Наносит урон после атакующего действия, в том числе при промахе."

    display_name = "Кровотечение"

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

        old_health = target.health
        damage = _deal_effect_damage(
            target,
            self.damage,
            self.damage_type,
        )
        self.triggers -= 1
        return EffectResult(
            damage=damage,
            messages=[feedback_message(
                f"Кровотечение наносит "
                f"{_effect_target_text(target)} {damage} урона.",
                damage_change(target, old_health, target.health, self.damage_type),
            )],
        )


class Regeneration(StatusEffect):
    """Positive status that restores HP at the start of the target's turn."""

    id = "regeneration"
    effect_type = EffectType.BUFF
    description = "Восстанавливает HP в начале хода, не выше максимума."

    stack_key = "regeneration"
    display_name = "Регенерация"

    def __init__(self, value, ticks=2):
        self.value = value
        self.ticks_remaining = ticks

    @property
    def is_expired(self):
        return self.ticks_remaining <= 0

    def stack(self, other):
        self.value = max(self.value, other.value)
        self.ticks_remaining = max(self.ticks_remaining, other.ticks_remaining)
        return True

    def on_turn_start(self, target):
        if self.is_expired:
            return EffectResult()
        old_health = target.health
        target.health = min(target.max_health, target.health + self.value)
        restored = target.health - old_health
        self.ticks_remaining -= 1
        return EffectResult(
            health_restored=restored,
            messages=[feedback_message(
                f"Регенерация восстанавливает {_effect_target_text(target)} "
                f"{restored} HP.",
                healing_change(target, old_health, target.health),
            )],
        )


class EffectCollection:
    def __init__(self):
        self.effects = []

    @property
    def active(self):
        return tuple(effect for effect in self.effects if not effect.is_expired)

    def get(self, effect_id):
        return next((effect for effect in self.active if effect.id == effect_id), None)

    def remove(self, effect):
        """Remove one exact instance (independent bleeds must remain independent)."""
        for index, existing in enumerate(self.effects):
            if existing is effect:
                del self.effects[index]
                return True
        return False

    def apply(self, effect, target):
        if not isinstance(effect, StatusEffect):
            raise TypeError("Expected a StatusEffect")
        if effect.instant:
            return effect.apply(target)
        self.add(effect)
        return EffectResult()

    def add(self, effect):
        if not isinstance(effect, StatusEffect):
            raise TypeError("Expected a StatusEffect")
        if effect.instant:
            raise ValueError("Instant effects require apply(effect, target)")
        self._remove_expired()
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
        return any(isinstance(effect, effect_type) for effect in self.active)

    def _remove_expired(self):
        self.effects = [
            effect for effect in self.effects
            if not effect.is_expired
        ]

    def on_turn_start(self, target):
        result = EffectResult()
        for effect in self.active:
            result.include(effect.on_turn_start(target))
        self._remove_expired()
        return result

    def on_action_performed(self, target, action):
        result = EffectResult()
        for effect in self.active:
            result.include(effect.on_action_performed(target, action))
        self._remove_expired()
        return result

    def on_turn_end(self, target):
        result = EffectResult()
        for effect in self.active:
            result.include(effect.on_turn_end(target))
        self._remove_expired()
        return result

    def modify_incoming_damage(self, damage, damage_type, skip_effect_ids=()):
        damage, _changes = self.modify_incoming_damage_with_trace(
            damage,
            damage_type,
            skip_effect_ids,
        )
        return damage

    def modify_incoming_damage_with_trace(
        self,
        damage,
        damage_type,
        skip_effect_ids=(),
    ):
        """Apply the shared mitigation chain and expose each actual change."""
        skip_effect_ids = frozenset(skip_effect_ids)
        changes = []
        for effect in self.active:
            if effect.id in skip_effect_ids:
                continue
            before = damage
            damage = effect.modify_incoming_damage(damage, damage_type)
            if damage != before:
                changes.append((effect, before, damage))
        return damage, tuple(changes)

    def modify_armor(self, armor):
        for effect in self.active:
            armor = effect.modify_armor(armor)
        return armor
