import pickle
import unittest
from unittest.mock import patch

from battle import CONSUMABLE_ACTION_KIND, create_player_turn_state, player_turn
from item import Heal
from player import Player
from world import World


class TestPermanentFlasks(unittest.TestCase):
    def test_new_player_starts_with_six_flasks_split_three_three(self):
        player = Player("Hero", None)
        self.assertEqual(player.total_flasks, 6)
        self.assertEqual((player.max_hp_flasks, player.max_mp_flasks), (3, 3))
        self.assertEqual((player.current_hp_flasks, player.current_mp_flasks), (3, 3))

    def test_using_flasks_spends_only_matching_current_charge(self):
        player = Player("Hero", None)
        player.health = 30
        player.mana = 0
        self.assertTrue(player.use_flask("hp"))
        self.assertEqual((player.health, player.current_hp_flasks), (70, 2))
        self.assertEqual(player.current_mp_flasks, 3)
        self.assertTrue(player.use_flask("mp"))
        self.assertEqual((player.mana, player.current_mp_flasks), (10, 2))

    def test_full_resource_or_zero_charges_does_not_spend_charge(self):
        player = Player("Hero", None)
        self.assertFalse(player.use_flask("hp"))
        self.assertEqual(player.current_hp_flasks, 3)
        player.health = 1
        player.current_hp_flasks = 0
        self.assertFalse(player.use_flask("hp"))
        self.assertEqual(player.health, 1)

    def test_each_flask_spends_one_action_point(self):
        player = Player("Hero", None)
        player.health = 30
        player.mana = 0
        state = create_player_turn_state(player)
        with patch("builtins.input", side_effect=["flask:hp", "flask:mp"]):
            player_turn(player, None, turn_state=state)
            player_turn(player, None, turn_state=state)
        self.assertEqual(state.action_points, 1)
        self.assertEqual((player.current_hp_flasks, player.current_mp_flasks), (2, 2))
        self.assertTrue(state.can_use(CONSUMABLE_ACTION_KIND))

    def test_flask_submenu_back_spends_nothing(self):
        player = Player("Hero", None)
        player.health -= 10
        state = create_player_turn_state(player)
        before = (state.action_points, player.current_hp_flasks,
                  player.current_mp_flasks, player.health, player.mana)

        with patch("battle.input", side_effect=["3", "0"]), \
                patch("battle.show_battle_screen") as screen:
            messages = player_turn(player, None, turn_state=state)

        self.assertEqual(
            (state.action_points, player.current_hp_flasks,
             player.current_mp_flasks, player.health, player.mana),
            before,
        )
        self.assertIn("возвращаетесь", messages[0])
        self.assertIn("0 - Назад", screen.call_args.kwargs["actions"])

    def test_distribution_uses_total_and_refills_current_charges(self):
        player = Player("Hero", None)
        player.total_flasks = 7
        player.max_hp_flasks = 4
        player.max_mp_flasks = 3
        player.current_hp_flasks = 1
        player.current_mp_flasks = 0
        self.assertTrue(player.set_flask_distribution(6))
        self.assertEqual((player.max_hp_flasks, player.max_mp_flasks), (6, 1))
        self.assertEqual((player.current_hp_flasks, player.current_mp_flasks), (6, 1))
        self.assertFalse(player.set_flask_distribution(8))
        self.assertFalse(player.set_flask_distribution(-1))

    def test_sleep_refills_using_current_distribution(self):
        player = Player("Hero", None)
        world = World()
        player.set_flask_distribution(5)
        player.current_hp_flasks = 1
        player.current_mp_flasks = 0
        world.start_new_day(player)
        self.assertEqual((player.current_hp_flasks, player.current_mp_flasks), (5, 1))

    def test_distribution_and_current_charges_survive_round_trip(self):
        player = Player("Hero", None)
        player.set_flask_distribution(4)
        player.current_hp_flasks = 2
        player.current_mp_flasks = 1
        restored = pickle.loads(pickle.dumps(player))
        self.assertEqual(restored.total_flasks, 6)
        self.assertEqual((restored.max_hp_flasks, restored.max_mp_flasks), (4, 2))
        self.assertEqual((restored.current_hp_flasks, restored.current_mp_flasks), (2, 1))

    def test_old_save_without_permanent_fields_gets_defaults(self):
        player = Player("Hero", None)
        for name in (
            "total_flasks", "max_hp_flasks", "max_mp_flasks",
            "current_hp_flasks", "current_mp_flasks",
        ):
            delattr(player, name)
        restored = pickle.loads(pickle.dumps(player))
        self.assertEqual(
            (restored.total_flasks, restored.max_hp_flasks,
             restored.max_mp_flasks, restored.current_hp_flasks,
             restored.current_mp_flasks),
            (6, 3, 3, 3, 3),
        )

    def test_legacy_potion_items_are_removed_on_load_and_cannot_be_added(self):
        player = Player("Hero", None)
        legacy_potion = Heal(40, 6)
        self.assertFalse(player.inventory.add_item(legacy_potion))
        player.inventory._slots[0] = legacy_potion

        restored = pickle.loads(pickle.dumps(player))

        self.assertEqual(restored.inventory.items, [])


if __name__ == "__main__":
    unittest.main()
