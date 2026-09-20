"""Player ability definitions, loadout state and turn-based cooldowns."""

from dataclasses import dataclass, field

from combat_feedback import damage_change, feedback_message
from combat_hit import resolve_hit
from damage import Damage_type
from effects import ATTACK_ACTION, NON_ATTACK_ACTION, Fortify


@dataclass(frozen=True)
class AbilityResult:
    success: bool
    messages: tuple = ()
    reason: str = ""


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    description: str
    class_requirement: str = None
    action_point_cost: int = 0
    cooldown: int = 0
    handler: object = None
    combat_action: object = NON_ATTACK_ACTION
    icon: str = "?"

    def apply(self, player, target):
        if self.handler is None:
            return AbilityResult(False, reason="У способности нет эффекта.")
        return self.handler(player, target)


@dataclass
class AbilityCooldown:
    """N blocks the next N player turns, including their entire duration."""

    turns_remaining: int
    locked_this_turn: bool = True

    def start_turn(self):
        if self.turns_remaining > 0:
            self.locked_this_turn = True
            self.turns_remaining -= 1
        else:
            self.locked_this_turn = False

    @property
    def active(self):
        return self.locked_this_turn or self.turns_remaining > 0

    @property
    def display_remaining(self):
        return max(1, self.turns_remaining) if self.active else 0


@dataclass
class AbilityBook:
    unlocked_ids: list = field(default_factory=list)
    slots: list = field(default_factory=lambda: [None, None, None])
    cooldowns: dict = field(default_factory=dict)

    def normalize(self):
        self.unlocked_ids = list(dict.fromkeys(
            ability_id for ability_id in self.unlocked_ids
            if ability_id in ABILITIES
        ))
        slots = list(self.slots[:3])
        slots.extend([None] * (3 - len(slots)))
        seen = set()
        for index, ability_id in enumerate(slots):
            if ability_id not in self.unlocked_ids or ability_id in seen:
                slots[index] = None
            elif ability_id is not None:
                seen.add(ability_id)
        self.slots = slots
        self.cooldowns = {
            ability_id: state
            for ability_id, state in self.cooldowns.items()
            if ability_id in self.unlocked_ids and isinstance(state, AbilityCooldown)
        }

    def unlock(self, ability_id):
        if ability_id not in ABILITIES or ability_id in self.unlocked_ids:
            return False
        self.unlocked_ids.append(ability_id)
        return True

    @property
    def unlocked(self):
        return tuple(ABILITIES[ability_id] for ability_id in self.unlocked_ids)

    def equip(self, ability_id, slot_index):
        if ability_id not in self.unlocked_ids or not 0 <= slot_index < 3:
            return False
        for index, equipped_id in enumerate(self.slots):
            if equipped_id == ability_id:
                self.slots[index] = None
        self.slots[slot_index] = ability_id
        return True

    def unequip(self, slot_index):
        if not 0 <= slot_index < 3 or self.slots[slot_index] is None:
            return False
        self.slots[slot_index] = None
        return True

    def is_equipped(self, ability_id):
        return ability_id in self.slots

    def start_turn(self):
        for state in tuple(self.cooldowns.values()):
            state.start_turn()
        self.cooldowns = {
            ability_id: state
            for ability_id, state in self.cooldowns.items()
            if state.active
        }

    def start_cooldown(self, ability):
        if ability.cooldown > 0:
            self.cooldowns[ability.id] = AbilityCooldown(ability.cooldown)

    def clear_cooldowns(self):
        self.cooldowns.clear()

    def cooldown_remaining(self, ability_id):
        state = self.cooldowns.get(ability_id)
        return state.display_remaining if state is not None else 0

    def is_on_cooldown(self, ability_id):
        state = self.cooldowns.get(ability_id)
        return bool(state and state.active)

    def check(self, player, ability_id):
        ability = ABILITIES.get(ability_id)
        if ability is None or ability_id not in self.unlocked_ids:
            return "Способность не открыта."
        if not self.is_equipped(ability_id):
            return "Способность не экипирована."
        class_id = getattr(getattr(player, "character_class", None), "id", None)
        if ability.class_requirement and ability.class_requirement != class_id:
            return "Способность недоступна этому классу."
        if self.is_on_cooldown(ability_id):
            remaining = self.cooldown_remaining(ability_id)
            return f"Перезарядка: ещё {remaining} ход."
        return ""


def _powerful_strike(player, target):
    messages = []
    for index, weapon in enumerate(player.attack_weapons()):
        if not target.is_alive():
            break
        damage_type = weapon.damage_type if weapon else Damage_type.PHYSICAL
        old_health = target.health

        def doubled_attack(current_weapon=weapon, first=index == 0):
            damage, critical = (
                player.attack(target)
                if first else player.attack(target, weapon=current_weapon)
            )
            return damage * 2, critical

        result = resolve_hit(
            target,
            doubled_attack,
            damage_type,
            on_hit=(lambda enemy, current=weapon: current.on_hit(
                enemy, source=player
            )) if weapon else None,
            armor_penetration=weapon.armor_penetration if weapon else 0,
        )
        if not result.hit:
            messages.append(
                f"Противник «{target.name}» уклоняется от «Мощного удара»."
            )
            continue
        messages.append(feedback_message(
            f"Мощный удар наносит противнику «{target.name}» "
            f"{result.damage} урона.",
            damage_change(
                target, old_health, target.health, damage_type, result.critical
            ),
        ))
        if result.critical:
            messages.append("Критический удар!")
    return AbilityResult(True, tuple(messages))


def _fortify(player, target):
    player.add_effect(Fortify())
    return AbilityResult(True, (
        "Вы укрепляетесь: текущая броня удвоена до начала следующего хода.",
    ))


ABILITIES = {
    ability.id: ability
    for ability in (
        Ability(
            "powerful_strike",
            "Мощный удар",
            "Наносит двойной урон относительно обычной атаки.",
            class_requirement="bruiser",
            action_point_cost=3,
            cooldown=2,
            handler=_powerful_strike,
            combat_action=ATTACK_ACTION,
            icon="М",
        ),
        Ability(
            "fortify",
            "Укрепиться",
            "Удваивает текущую броню до начала следующего хода игрока.",
            class_requirement="bruiser",
            action_point_cost=3,
            cooldown=2,
            handler=_fortify,
            combat_action=NON_ATTACK_ACTION,
            icon="У",
        ),
    )
}


CLASS_ABILITY_IDS = {
    "bruiser": ("powerful_strike", "fortify"),
    "daredevil": (),
    "herald": (),
}


def grant_class_abilities(player, class_id):
    for ability_id in CLASS_ABILITY_IDS.get(class_id, ()):
        player.abilities.unlock(ability_id)
