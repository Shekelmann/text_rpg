"""Weapon artwork lookup. No Pillow/Tk dependency at game runtime."""

from pathlib import Path
from rarity import Rarity


ICON_SIZE = 64
WEAPON_ASSETS = Path(__file__).resolve().parent / "assets" / "items" / "weapons"


def weapon_icon_path(weapon_or_id, rarity=None):
    """Resolve an instance, WEAPONS key or ITEMS alias; unknown artwork -> None.

    Instance rarity is read on each call, so loot rarity changes cannot leave a
    stale path. Aliases come from the existing registry, not a second ID table.
    """
    weapon = weapon_or_id
    if isinstance(weapon, str):
        from objects import WEAPONS, ITEMS
        weapon = WEAPONS.get(weapon) or ITEMS.get(weapon)
    family = getattr(weapon, "icon_id", None)
    if not family:
        return None
    rarity = getattr(weapon, "rarity", Rarity.COMMON) if rarity is None else rarity
    if not isinstance(rarity, Rarity):
        raise TypeError("rarity must be a Rarity enum member")
    # IDs are file stems, never arbitrary filesystem paths.
    if not all(c.isascii() and (c.isalnum() or c == "_") for c in family):
        return None
    path = WEAPON_ASSETS / "icons" / f"{family}_{rarity.name.lower()}.png"
    return path if path.is_file() else None
