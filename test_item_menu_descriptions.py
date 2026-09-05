import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from interface import (
    _buy_from_merchant,
    _sell_to_merchant,
    _show_category,
    format_item_for_menu,
)
from npcs import HEINRICH
from objects import create_item
from player import Player


class TestItemMenuDescriptions(unittest.TestCase):
    def test_weapon_and_healing_item_use_real_values(self):
        self.assertEqual(
            format_item_for_menu(create_item("sword")),
            "Меч (урон: 3–7)",
        )
        self.assertEqual(
            format_item_for_menu(create_item("heal")),
            "Зелье лечения (восполняет 10 здоровья)",
        )

    @patch("builtins.input", return_value="0")
    def test_inventory_and_equipment_lists_show_descriptions(self, _mock_input):
        player = Player("Hero", None)
        sword = create_item("sword")
        player.inventory.add_item(sword)

        output = io.StringIO()
        with redirect_stdout(output):
            _show_category(player, "weapon", "Оружие")

        self.assertIn("Меч (урон: 3–7)", output.getvalue())

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", return_value="0")
    def test_purchase_list_shows_item_descriptions(
        self,
        _mock_input,
        _mock_clear,
        mock_show_box,
    ):
        player = Player("Hero", None)

        _buy_from_merchant(player, HEINRICH)

        lines = mock_show_box.call_args.args[0]
        self.assertTrue(any("Меч (урон: 3–7)" in line for line in lines if line))
        self.assertTrue(
            any(
                "Зелье лечения (восполняет 10 здоровья)" in line
                for line in lines
                if line
            )
        )

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", return_value="0")
    def test_sale_list_shows_item_descriptions(
        self,
        _mock_input,
        _mock_clear,
        mock_show_box,
    ):
        player = Player("Hero", None)
        potion = create_item("heal")
        player.inventory.add_item(potion)

        _sell_to_merchant(player, HEINRICH)

        lines = mock_show_box.call_args.args[0]
        self.assertTrue(
            any(
                "Зелье лечения (восполняет 10 здоровья)" in line
                for line in lines
                if line
            )
        )


if __name__ == "__main__":
    unittest.main()
