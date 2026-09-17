import unittest
from unittest.mock import patch

from interface import configure_flask_distribution, trade_with_merchant
from main import get_location_menu_options, interact_with_npc
from npc import Healer, Merchant, NPC, TradeResult
from npcs import GREG, HEINRICH
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

    def test_greg_is_a_healer_in_three_stumps_tavern(self):
        world = World()
        self.assertIsInstance(GREG, Healer)
        self.assertEqual(GREG.name, "Знахарь Грег")
        self.assertIn("greg", world.get_location_npc_ids("tavern"))
        self.assertIn(
            "Поговорить: Знахарь Грег",
            [label for _, label in get_location_menu_options(world, "tavern")],
        )

    @patch("main.trade_with_merchant")
    def test_generic_npc_dispatch_opens_merchant_ui(self, mock_trade):
        player = Player("Hero", None)

        self.assertTrue(interact_with_npc(player, HEINRICH))
        mock_trade.assert_called_once_with(player, HEINRICH)

    @patch("main.manage_flasks_with_greg")
    def test_greg_dispatch_opens_flask_menu(self, mock_manage):
        player = Player("Hero", None)
        self.assertTrue(interact_with_npc(player, GREG))
        mock_manage.assert_called_once_with(player, GREG)


class TestMerchantTrading(unittest.TestCase):
    def setUp(self):
        self.player = Player("Hero", None)
        self.player.gold = 100

    def test_heinrich_has_basic_assortment(self):
        self.assertGreater(len(HEINRICH.assortment), 0)
        for item_id, price in HEINRICH.assortment.items():
            self.assertIn(item_id, ITEMS)
            self.assertGreater(price, 0)
        self.assertNotIn("heal", HEINRICH.assortment)
        self.assertNotIn("mana", HEINRICH.assortment)

    def test_buying_item_spends_gold_and_adds_independent_item(self):
        item_id = "sword"
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

        result = HEINRICH.buy_item(self.player, "sword")

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
        item = create_item("leather_armor")

        self.assertEqual(item.price, ITEMS["leather_armor"].price)

    @patch("interface.show_box")
    @patch("interface.clear")
    @patch("builtins.input", side_effect=["1", "1", "1", "0", "0"])
    def test_trade_ui_can_buy_from_heinrich(
        self,
        _mock_input,
        _mock_clear,
        _mock_show_box,
    ):
        price = HEINRICH.get_buy_price("sword")

        trade_with_merchant(self.player, HEINRICH)

        self.assertEqual(self.player.gold, 100 - price)
        self.assertEqual(len(self.player.inventory.get_weapons()), 1)


class TestGregFlaskAllocation(unittest.TestCase):
    @patch("interface.request_flask_distribution", return_value=(True, 5))
    def test_gui_allocation_applies_mirrored_split_and_refills(self, _request):
        player = Player("Hero", None)
        player.current_hp_flasks = 0
        player.current_mp_flasks = 0

        self.assertTrue(configure_flask_distribution(player))
        self.assertEqual((player.max_hp_flasks, player.max_mp_flasks), (5, 1))
        self.assertEqual((player.current_hp_flasks, player.current_mp_flasks), (5, 1))

    @patch("interface.request_flask_distribution", return_value=(True, None))
    def test_cancel_keeps_existing_distribution(self, _request):
        player = Player("Hero", None)

        self.assertFalse(configure_flask_distribution(player))
        self.assertEqual((player.max_hp_flasks, player.max_mp_flasks), (3, 3))


if __name__ == "__main__":
    unittest.main()
