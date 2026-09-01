import random


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
