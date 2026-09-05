import unittest
from unittest.mock import patch

from interface import _buy_from_merchant, _sell_to_merchant, _show_category
from npcs import HEINRICH
from objects import create_item
from player import Player


class TestEquipmentMenuNavigation(unittest.TestCase):
    @patch("builtins.input", side_effect=["1", "0"])
    def test_weapon_equips_immediately_and_stays_in_category(self, mock_input):
        player = Player("Hero", None)
        sword = create_item("sword")
        player.inventory.add_item(sword)

        result = _show_category(player, "weapon", "Weapons")

        self.assertIsNone(result)
        self.assertIs(player.main_hand, sword)
        self.assertNotIn(sword, player.inventory.items)
        self.assertEqual(mock_input.call_count, 2)

    @patch("builtins.input", side_effect=["1", "0"])
    def test_armor_equips_immediately_and_stays_in_category(self, mock_input):
        player = Player("Hero", None)
        helmet = create_item("leather_helmet")
        player.inventory.add_item(helmet)

        result = _show_category(player, "armor", "Armor")

        self.assertIsNone(result)
        self.assertIs(player.head, helmet)
        self.assertNotIn(helmet, player.inventory.items)
        self.assertEqual(mock_input.call_count, 2)


class TestTradeMenuNavigation(unittest.TestCase):
    def setUp(self):
        self.player = Player("Hero", None)
        self.player.gold = 100

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", side_effect=["1", "1", "0"])
    def test_buy_redraws_same_menu_with_updated_gold(
        self,
        mock_input,
        _mock_clear,
        mock_show_box,
    ):
        price = HEINRICH.get_buy_price("heal")

        result = None
        while result is not None or mock_input.call_count == 0:
            result = _buy_from_merchant(self.player, HEINRICH)

        self.assertEqual(self.player.gold, 100 - price)
        self.assertEqual(mock_show_box.call_count, 2)
        refreshed_lines = mock_show_box.call_args_list[1].args[0]
        self.assertTrue(
            any(str(self.player.gold) in line for line in refreshed_lines if line)
        )

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", side_effect=["1", "1", "0"])
    def test_sell_redraws_same_menu_after_last_item_is_removed(
        self,
        mock_input,
        _mock_clear,
        mock_show_box,
    ):
        item = create_item("heal")
        self.player.inventory.add_item(item)
        expected_gold = self.player.gold + HEINRICH.get_sell_price(item)

        result = None
        while result is not None or mock_input.call_count == 0:
            result = _sell_to_merchant(self.player, HEINRICH)

        self.assertEqual(self.player.gold, expected_gold)
        self.assertNotIn(item, self.player.inventory.items)
        self.assertEqual(mock_show_box.call_count, 2)
        refreshed_lines = mock_show_box.call_args_list[1].args[0]
        self.assertTrue(any(str(expected_gold) in line for line in refreshed_lines if line))


if __name__ == "__main__":
    unittest.main()
