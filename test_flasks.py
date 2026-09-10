import unittest
from unittest.mock import patch
from objects import create_item, ENEMY_LOOT
from player import Player
from item import Heal
from npcs import HEINRICH
from npc import TradeResult
from battle import create_player_turn_state, player_turn, CONSUMABLE_ACTION_KIND


class TestFlasks(unittest.TestCase):
    def test_purchase_flasks_with_full_backpack_and_restore(self):
        player = Player('Hero', None)
        for _ in range(20):
            player.inventory.add_item(create_item('dagger'))
        player.gold = 100
        player.health = 30
        player.mana = 0
        for item_id, resource, amount in (('heal', 'hp', 40), ('mana', 'mp', 10)):
            self.assertEqual(HEINRICH.buy_item(player, item_id), TradeResult.SUCCESS)
            self.assertEqual(player.flasks[resource].count, 1)
            self.assertEqual(player.flasks[resource].restore_amount, amount)
            self.assertTrue(player.use_flask(resource))
            self.assertEqual(player.flasks[resource].count, 0)
            self.assertFalse(player.use_flask(resource))
        self.assertEqual((player.health, player.mana), (70, 10))
        self.assertEqual(len(player.inventory.items), 20)
        self.assertEqual(player.gold, 88)

    def test_mana_loot_uses_catalog_and_flask_storage(self):
        from objects import generate_loot, ITEMS
        from loot import LootTable
        self.assertTrue(all(any(e.item_id == "mana" for e in ENEMY_LOOT[key].entries)
                            for key in ("goblin", "demon")))
        drops = generate_loot(LootTable.from_mapping({"mana": 1}))
        player = Player("Hero", None)
        for item in drops:
            self.assertIsNot(item, ITEMS["mana"])
            self.assertTrue(player.inventory.add_item(item))
        self.assertEqual(player.flasks["mp"].count, 1)
        self.assertEqual(player.inventory.items, [])

    def test_full_resource_keeps_charge_and_special_consumable_keeps_slot(self):
        player = Player('Hero', None)
        for item_id, resource in (('heal', 'hp'), ('mana', 'mp')):
            player.inventory.add_item(create_item(item_id))
            self.assertFalse(player.use_flask(resource))
            self.assertEqual(player.flasks[resource].count, 1)
        special = Heal(17)
        player.inventory.add_item(special)
        self.assertEqual(player.inventory.items, [special])
        player.mana = 7
        self.assertTrue(player.use_flask('mp'))
        self.assertEqual(player.mana, player.max_mana)

    def test_flasks_share_one_battle_consumable_action(self):
        player = Player('Hero', None)
        player.health = 30
        player.mana = 0
        for item_id in ('heal', 'mana'):
            player.inventory.add_item(create_item(item_id))
        state = create_player_turn_state(player)
        with patch('builtins.input', side_effect=['flask:hp', 'flask:mp']):
            player_turn(player, None, turn_state=state)
            player_turn(player, None, turn_state=state)
        self.assertEqual((player.health, player.mana), (70, 0))
        self.assertFalse(state.can_use(CONSUMABLE_ACTION_KIND))
        self.assertEqual(player.flasks['mp'].count, 1)
        with patch('builtins.input', return_value='flask:mp'):
            player_turn(player, None, turn_state=create_player_turn_state(player))
        self.assertEqual(player.mana, 10)


if __name__ == '__main__':
    unittest.main()
