import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from affix_pool import WEAPON_AFFIX_POOL
from battle import distribute_loot
from interface import configure_loot_filter, show_ground_loot
from loot import LootFilter
from main import get_location_menu_options
from objects import create_item
from player import Player
from rarity import Rarity
from world import World


class TestLootFilter(unittest.TestCase):
    def test_filter_is_available_and_configurable_through_location_menu(self):
        player = Player("Hero", None)
        world = World()

        self.assertIn(
            "Настроить лут-фильтр",
            [label for _, label in get_location_menu_options(world, "village")],
        )
        with patch("builtins.input", side_effect=["1", "2", "0"]):
            configure_loot_filter(player)

        self.assertEqual(player.loot_filter.rarities, {Rarity.RARE})

    def test_filters_by_rarity_and_item_type(self):
        loot_filter = LootFilter(
            rarities={Rarity.RARE},
            item_types={"weapon"},
        )
        weapon = create_item("sword")
        weapon.rarity = Rarity.RARE
        armor = create_item("leather_helmet")
        armor.rarity = Rarity.RARE

        self.assertTrue(loot_filter.matches(weapon))
        self.assertFalse(loot_filter.matches(armor))
        weapon.rarity = Rarity.COMMON
        self.assertFalse(loot_filter.matches(weapon))

    def test_filters_by_at_least_n_selected_affixes(self):
        selected = WEAPON_AFFIX_POOL[:2]
        weapon = create_item("sword")
        weapon.rarity = Rarity.RARE
        weapon.set_affixes(selected)

        self.assertTrue(LootFilter(
            affix_ids={affix.id for affix in selected},
            minimum_affix_matches=2,
        ).matches(weapon))
        self.assertFalse(LootFilter(
            affix_ids={selected[0].id, "missing"},
            minimum_affix_matches=2,
        ).matches(weapon))

    def test_legendary_always_matches(self):
        item = create_item("wolf_pelt")
        item.rarity = Rarity.LEGENDARY
        loot_filter = LootFilter(
            rarities={Rarity.COMMON},
            item_types={"weapon"},
            affix_ids={"missing"},
            minimum_affix_matches=5,
        )

        self.assertTrue(loot_filter.matches(item))

    def test_hidden_loot_is_still_added_to_inventory(self):
        player = Player("Hero", None)
        player.loot_filter.rarities = {Rarity.EPIC}
        item = create_item("wolf_pelt")
        output = io.StringIO()

        with redirect_stdout(output):
            distribute_loot(player, [item])

        self.assertIn(item, player.inventory.items)
        self.assertIn("Скрыто предметов: 1.", output.getvalue())
        self.assertNotIn("Вы получили:", output.getvalue())


class TestGroundLoot(unittest.TestCase):
    def test_full_inventory_leaves_item_in_location_until_taken(self):
        player = Player("Hero", None)
        player.inventory.size = 0
        world = World()
        item = create_item("wolf_pelt")

        distribute_loot(player, [item], world, "forest")
        player.current_location = "village"
        player.current_location = "forest"

        self.assertEqual(world.get_ground_loot("forest"), (item,))
        self.assertIn(
            "Выпавшие предметы",
            [label for _, label in get_location_menu_options(world, "forest")],
        )

        player.inventory.size = 1
        with patch("builtins.input", side_effect=["1", "0"]):
            show_ground_loot(player, world, "forest")

        self.assertIn(item, player.inventory.items)
        self.assertEqual(world.get_ground_loot("forest"), ())

    def test_ground_loot_display_respects_filter_without_removing_items(self):
        player = Player("Hero", None)
        player.loot_filter.rarities = {Rarity.EPIC}
        world = World()
        item = create_item("wolf_pelt")
        world.add_ground_loot("forest", item)
        output = io.StringIO()

        with redirect_stdout(output), patch("builtins.input", return_value="0"):
            show_ground_loot(player, world, "forest")

        self.assertIn("Скрыто предметов: 1.", output.getvalue())
        self.assertEqual(world.get_ground_loot("forest"), (item,))


if __name__ == "__main__":
    unittest.main()
