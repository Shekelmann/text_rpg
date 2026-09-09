import random

from rarity import Rarity


ENEMY_ITEM_DROP_CHANCE = 0.5

ENEMY_RARITY_WEIGHTS = (
    (1, 3, {
        Rarity.COMMON: 0.75,
        Rarity.RARE: 0.23,
        Rarity.EPIC: 0.02,
    }),
    (4, 7, {
        Rarity.COMMON: 0.45,
        Rarity.RARE: 0.45,
        Rarity.EPIC: 0.10,
    }),
    (8, 12, {
        Rarity.COMMON: 0.20,
        Rarity.RARE: 0.55,
        Rarity.EPIC: 0.25,
    }),
)


def get_enemy_rarity_weights(level):
    for minimum, maximum, weights in ENEMY_RARITY_WEIGHTS:
        if minimum <= level <= maximum:
            return weights
    if level < ENEMY_RARITY_WEIGHTS[0][0]:
        return ENEMY_RARITY_WEIGHTS[0][2]
    return ENEMY_RARITY_WEIGHTS[-1][2]


def roll_item_rarity(level, rng=None):
    rng = random if rng is None else rng
    weights = get_enemy_rarity_weights(level)
    return rng.choices(
        list(weights.keys()),
        weights=weights.values(),
    )[0]


class LootFilter:
    def __init__(
        self,
        rarities=None,
        item_types=None,
        affix_ids=None,
        minimum_affix_matches=1,
    ):
        self.rarities = set(rarities or ())
        self.item_types = set(item_types or ())
        self.affix_ids = set(affix_ids or ())
        self.minimum_affix_matches = max(1, int(minimum_affix_matches))

    def matches(self, item):
        if getattr(item, "rarity", Rarity.COMMON) == Rarity.LEGENDARY:
            return True
        if self.rarities and getattr(item, "rarity", None) not in self.rarities:
            return False
        if self.item_types and getattr(item, "item_type", None) not in self.item_types:
            return False
        if self.affix_ids:
            matching_affixes = sum(
                affix.id in self.affix_ids
                for affix in getattr(item, "affixes", ())
            )
            if matching_affixes < self.minimum_affix_matches:
                return False
        return True

    def reset(self):
        self.rarities.clear()
        self.item_types.clear()
        self.affix_ids.clear()
        self.minimum_affix_matches = 1


class LootEntry:
    def __init__(self, item_id, chance):
        if not 0 <= chance <= 1:
            raise ValueError(
                f"Шанс выпадения должен быть от 0 до 1: {item_id}={chance}"
            )
        self.item_id = item_id
        self.chance = chance


class LootTable:
    def __init__(self, entries=None):
        self.entries = []
        if not entries:
            return

        for entry in entries:
            if isinstance(entry, LootEntry):
                self.entries.append(entry)
            elif isinstance(entry, (tuple, list)) and len(entry) == 2:
                self.entries.append(LootEntry(entry[0], entry[1]))
            else:
                raise TypeError(f"Некорректная запись лута: {entry}")

    @classmethod
    def from_mapping(cls, mapping):
        return cls(
            LootEntry(item_id, chance)
            for item_id, chance in mapping.items()
        )

    def copy(self):
        return LootTable(
            LootEntry(entry.item_id, entry.chance)
            for entry in self.entries
        )

    def roll(self, rng=None):
        rng = random if rng is None else rng
        dropped = []
        for entry in self.entries:
            if entry.chance <= 0:
                continue
            if entry.chance >= 1 or rng.random() < entry.chance:
                dropped.append(entry.item_id)
        return dropped
