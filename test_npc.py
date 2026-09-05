import unittest
from unittest.mock import patch

from interface import trade_with_merchant
from main import get_location_menu_options, interact_with_npc
from npc import Merchant, NPC, TradeResult
from npcs import HEINRICH
from objects import ITEMS, create_item
from player import Player
from world import World


class TestNPCStructure(unittest.TestCase):
    def test_base_npc_supports_other_roles(self):
        npc = NPC("future_smith", "Кузнец", "blacksmith")

        self.assertEqual(npc.id, "future_smith")
        self.assertEqual(npc.name, "Кузнец")
        self.assertEqual(npc.role, "blacksmith")

    def test_heinrich_is_a_merchant_in_three_stumps_tavern(self):
        world = World()

        self.assertIsInstance(HEINRICH, Merchant)
        self.assertEqual(HEINRICH.name, "Генрих")
        self.assertIn("heinrich", world.get_location_npc_ids("tavern"))
        self.assertNotIn("heinrich", world.get_location_npc_ids("village"))

        tavern_labels = [
            label
            for _, label in get_location_menu_options(world, "tavern")
        ]
        self.assertIn("Поговорить: Генрих", tavern_labels)

    @patch("main.trade_with_merchant")
    def test_generic_npc_dispatch_opens_merchant_ui(self, mock_trade):
        player = Player("Hero", None)

        self.assertTrue(interact_with_npc(player, HEINRICH))
        mock_trade.assert_called_once_with(player, HEINRICH)


class TestMerchantTrading(unittest.TestCase):
    def setUp(self):
        self.player = Player("Hero", None)
        self.player.gold = 100

    def test_heinrich_has_basic_assortment(self):
        self.assertGreater(len(HEINRICH.assortment), 0)
        for item_id, price in HEINRICH.assortment.items():
            self.assertIn(item_id, ITEMS)
            self.assertGreater(price, 0)

    def test_buying_item_spends_gold_and_adds_independent_item(self):
        item_id = "heal"
        price = HEINRICH.get_buy_price(item_id)

        result = HEINRICH.buy_item(self.player, item_id)

        self.assertEqual(result, TradeResult.SUCCESS)
        self.assertEqual(self.player.gold, 100 - price)
        self.assertEqual(len(self.player.inventory.items), 1)
        self.assertEqual(self.player.inventory.items[0].name, ITEMS[item_id].name)
        self.assertIsNot(self.player.inventory.items[0], ITEMS[item_id])

    def test_cannot_buy_without_enough_gold(self):
        self.player.gold = 0

        result = HEINRICH.buy_item(self.player, "sword")

        self.assertEqual(result, TradeResult.NOT_ENOUGH_GOLD)
        self.assertEqual(self.player.gold, 0)
        self.assertEqual(self.player.inventory.items, [])

    def test_cannot_buy_when_inventory_is_full(self):
        self.player.inventory.size = 0

        result = HEINRICH.buy_item(self.player, "heal")

        self.assertEqual(result, TradeResult.INVENTORY_FULL)
        self.assertEqual(self.player.gold, 100)
        self.assertEqual(self.player.inventory.items, [])

    def test_cannot_buy_item_outside_assortment(self):
        result = HEINRICH.buy_item(self.player, "axe_2h")

        self.assertEqual(result, TradeResult.NOT_AVAILABLE)
        self.assertEqual(self.player.gold, 100)
        self.assertEqual(self.player.inventory.items, [])

    def test_selling_item_adds_gold_and_removes_item(self):
        item = create_item("sword")
        self.player.inventory.add_item(item)
        expected_gold = 100 + HEINRICH.get_sell_price(item)

        result = HEINRICH.sell_item(self.player, item)

        self.assertEqual(result, TradeResult.SUCCESS)
        self.assertEqual(self.player.gold, expected_gold)
        self.assertNotIn(item, self.player.inventory.items)

    def test_cannot_sell_item_not_owned_by_player(self):
        item = create_item("sword")

        result = HEINRICH.sell_item(self.player, item)

        self.assertEqual(result, TradeResult.ITEM_NOT_OWNED)
        self.assertEqual(self.player.gold, 100)

    def test_item_factory_preserves_base_price(self):
        item = create_item("leather_chest")

        self.assertEqual(item.price, ITEMS["leather_chest"].price)

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", side_effect=["1", "1", "1", "0", "0"])
    def test_trade_ui_can_buy_from_heinrich(
        self,
        _mock_input,
        _mock_clear,
        _mock_show_box,
    ):
        price = HEINRICH.get_buy_price("heal")

        trade_with_merchant(self.player, HEINRICH)

        self.assertEqual(self.player.gold, 100 - price)
        self.assertEqual(len(self.player.inventory.items), 1)
        self.assertEqual(self.player.inventory.items[0].name, "Зелье лечения")


if __name__ == "__main__":
    unittest.main()
