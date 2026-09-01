import unittest
from item import Armor, Heal
from loot import LootEntry, LootTable
from objects import ENEMY_LOOT, ITEMS, create_item, generate_loot, get_loot_table
from weapon import Weapon


class SequenceRng:
    def __init__(self, values):
        self.values = list(values)
        self.index = 0

    def random(self):
        value = self.values[self.index]
        self.index += 1
        return value


class AlwaysDropRng:
    def random(self):
        return 0.0


class NeverDropRng:
    def random(self):
        return 1.0


class TestLootTable(unittest.TestCase):
    def test_entry_keeps_item_id_and_chance(self):
        entry = LootEntry("heal", 0.5)
        self.assertEqual(entry.item_id, "heal")
        self.assertEqual(entry.chance, 0.5)

    def test_chance_must_be_between_zero_and_one(self):
        with self.assertRaises(ValueError):
            LootEntry("heal", -0.1)
        with self.assertRaises(ValueError):
            LootEntry("heal", 1.1)

    def test_table_holds_multiple_items(self):
        table = LootTable.from_mapping({
            "heal": 0.5,
            "sword": 0.2,
            "leather_helmet": 0.1,
        })
        self.assertEqual(
            [(entry.item_id, entry.chance) for entry in table.entries],
            [("heal", 0.5), ("sword", 0.2), ("leather_helmet", 0.1)],
        )

    def test_table_accepts_pairs_and_entries(self):
        table = LootTable([
            ("heal", 1.0),
            LootEntry("sword", 0.0),
        ])
        self.assertEqual(table.entries[0].item_id, "heal")
        self.assertEqual(table.entries[1].item_id, "sword")

    def test_guaranteed_and_impossible_drops(self):
        table = LootTable([
            ("heal", 1.0),
            ("sword", 0.0),
        ])
        self.assertEqual(table.roll(AlwaysDropRng()), ["heal"])
        self.assertEqual(table.roll(NeverDropRng()), ["heal"])

    def test_each_item_rolls_independently(self):
        table = LootTable.from_mapping({
            "heal": 0.5,
            "sword": 0.2,
            "leather_helmet": 0.8,
        })
        dropped = table.roll(SequenceRng([0.49, 0.20, 0.79]))
        self.assertEqual(dropped, ["heal", "leather_helmet"])

    def test_empty_table_drops_nothing(self):
        self.assertEqual(LootTable().roll(AlwaysDropRng()), [])

    def test_copy_is_independent_of_original(self):
        table = LootTable.from_mapping({"heal": 1.0})
        copied = table.copy()
        copied.entries.append(LootEntry("sword", 1.0))
        self.assertEqual([entry.item_id for entry in table.entries], ["heal"])
        self.assertEqual(
            [entry.item_id for entry in copied.entries],
            ["heal", "sword"],
        )


class TestEnemyLootTables(unittest.TestCase):
    def test_existing_tables_keep_current_entries(self):
        self.assertEqual(
            [(entry.item_id, entry.chance) for entry in ENEMY_LOOT["goblin"].entries],
            [
                ("heal", 0.5),
                ("sword", 0.5),
                ("leather_helmet", 0.5),
                ("leather_chest", 0.5),
                ("leather_gloves", 0.5),
                ("leather_boots", 0.5),
            ],
        )
        self.assertEqual(
            [(entry.item_id, entry.chance) for entry in ENEMY_LOOT["skeleton"].entries],
            [
                ("heal", 0.5),
                ("axe", 0.2),
                ("leather_helmet", 0.5),
                ("leather_chest", 0.5),
                ("leather_gloves", 0.5),
                ("leather_boots", 0.5),
            ],
        )

    def test_tables_are_registered_per_enemy(self):
        self.assertIsNot(ENEMY_LOOT["goblin"], ENEMY_LOOT["skeleton"])
        goblin_ids = [entry.item_id for entry in ENEMY_LOOT["goblin"].entries]
        skeleton_ids = [entry.item_id for entry in ENEMY_LOOT["skeleton"].entries]
        self.assertIn("sword", goblin_ids)
        self.assertNotIn("sword", skeleton_ids)
        self.assertIn("axe", skeleton_ids)
        self.assertNotIn("axe", goblin_ids)

    def test_missing_enemy_gets_empty_table(self):
        table = get_loot_table("wolf")
        self.assertEqual(table.roll(AlwaysDropRng()), [])

    def test_new_enemy_table_can_be_added_without_changing_class(self):
        ENEMY_LOOT["test_enemy"] = LootTable.from_mapping({"dagger": 1.0})
        try:
            table = get_loot_table("test_enemy")
            self.assertEqual(table.roll(AlwaysDropRng()), ["dagger"])
        finally:
            del ENEMY_LOOT["test_enemy"]

    def test_get_loot_table_does_not_mutate_catalog(self):
        table = get_loot_table("goblin")
        table.entries.clear()
        self.assertGreater(len(ENEMY_LOOT["goblin"].entries), 0)

    def test_all_registered_loot_ids_exist_in_catalog(self):
        for enemy_id, table in ENEMY_LOOT.items():
            for entry in table.entries:
                self.assertIn(entry.item_id, ITEMS, enemy_id)


class TestGenerateLoot(unittest.TestCase):
    def test_generate_loot_creates_independent_items_of_different_types(self):
        table = LootTable.from_mapping({
            "heal": 1.0,
            "sword": 1.0,
            "leather_helmet": 1.0,
        })
        first = generate_loot(table, AlwaysDropRng())
        second = generate_loot(table, AlwaysDropRng())

        self.assertEqual(len(first), 3)
        self.assertIsInstance(first[0], Heal)
        self.assertIsInstance(first[1], Weapon)
        self.assertIsInstance(first[2], Armor)
        self.assertEqual(first[0].item_type, "potion")
        self.assertEqual(first[1].item_type, "weapon")
        self.assertEqual(first[2].item_type, "armor")

        self.assertIsNot(first[0], second[0])
        self.assertIsNot(first[1], ITEMS["sword"])
        self.assertIsNot(first[2], ITEMS["leather_helmet"])

    def test_generate_loot_uses_create_item(self):
        table = LootTable([("heal", 1.0)])
        items = generate_loot(table, AlwaysDropRng())
        created = create_item("heal")
        self.assertEqual(items[0].name, created.name)
        self.assertEqual(items[0].heal, created.heal)
        self.assertIsNot(items[0], created)

    def test_generate_loot_none_returns_empty_list(self):
        self.assertEqual(generate_loot(None), [])


if __name__ == "__main__":
    unittest.main()
