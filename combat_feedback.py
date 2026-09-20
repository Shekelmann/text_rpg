"""Visual-only combat feedback attached to otherwise ordinary log messages."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HealthChange:
    target: str
    before: int
    after: int
    amount: int
    kind: str
    damage_type: str = ""
    critical: bool = False

    def as_dict(self):
        return asdict(self)


class CombatMessage(str):
    """A string-compatible message with optional non-gameplay UI metadata."""

    def __new__(cls, text, *health_changes):
        message = super().__new__(cls, text)
        message.health_changes = tuple(health_changes)
        return message


def target_role(target):
    return "player" if getattr(target, "is_player", False) else "enemy"


def damage_change(target, before, after, damage_type=None, critical=False):
    return HealthChange(
        target=target_role(target),
        before=int(before),
        after=int(after),
        amount=max(0, int(before) - int(after)),
        kind="damage",
        damage_type=getattr(damage_type, "name", "") if damage_type else "",
        critical=bool(critical),
    )


def healing_change(target, before, after):
    return HealthChange(
        target=target_role(target),
        before=int(before),
        after=int(after),
        amount=max(0, int(after) - int(before)),
        kind="healing",
    )


def feedback_message(text, *changes):
    return CombatMessage(text, *(change for change in changes if change.amount > 0))
