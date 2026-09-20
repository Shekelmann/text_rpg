import pickle
import unittest
from unittest.mock import patch

from ability import ABILITIES
from battle import (
    ABILITY_ACTION_KIND,
    ATTACK_ACTION_KIND,
    PlayerTurnState,
    get_player_turn_actions,
    player_turn,
    use_ability_action,
)
from character_class import CLASSES
from damage import Damage_type
from enemy import Enemy
from effects import NON_ATTACK_ACTION
from gui_views import ability_snapshot
from item import Armor
from player import Player


class TestPlayerAbilities(unittest.TestCase):
    def make_bruiser(self):
        return Player("Бугай", None, CLASSES["bruiser"])

    def test_only_bruiser_receives_current_class_abilities(self):
        bruiser = self.make_bruiser()
        self.assertEqual(
            tuple(ability.id for ability in bruiser.abilities.unlocked),
            ("powerful_strike", "fortify"),
        )
        for class_id in ("daredevil", "herald"):
            player = Player(class_id, None, CLASSES[class_id])
            self.assertEqual(player.abilities.unlocked, ())

    def test_three_slots_can_equip_replace_unequip_and_survive_save(self):
        player = self.make_bruiser()
        self.assertEqual(len(player.abilities.slots), 3)
        self.assertTrue(player.equip_ability("powerful_strike", 0))
        self.assertTrue(player.equip_ability("fortify", 1))
        self.assertTrue(player.equip_ability("fortify", 0))
        self.assertEqual(player.abilities.slots, ["fortify", None, None])
        self.assertTrue(player.unequip_ability(0))
        self.assertEqual(player.abilities.slots, [None, None, None])

        player.equip_ability("powerful_strike", 2)
        restored = pickle.loads(pickle.dumps(player))
        self.assertEqual(restored.abilities.slots, [None, None, "powerful_strike"])
        self.assertEqual(
            tuple(ability.id for ability in restored.abilities.unlocked),
            ("powerful_strike", "fortify"),
        )

    def test_loadout_cannot_change_during_combat(self):
        player = self.make_bruiser()
        player.equip_ability("powerful_strike", 0)
        player.in_combat = True
        self.assertFalse(player.equip_ability("fortify", 1))
        self.assertFalse(player.unequip_ability(0))
        self.assertEqual(player.abilities.slots, ["powerful_strike", None, None])

    def test_old_save_gets_class_abilities_and_empty_slots(self):
        player = self.make_bruiser()
        del player.abilities

        restored = pickle.loads(pickle.dumps(player))

        self.assertEqual(len(restored.abilities.slots), 3)
        self.assertEqual(restored.abilities.slots, [None, None, None])
        self.assertEqual(
            tuple(ability.id for ability in restored.abilities.unlocked),
            ("powerful_strike", "fortify"),
        )

    def test_powerful_strike_doubles_normal_roll_before_enemy_armor(self):
        player = self.make_bruiser()
        player.equip_ability("powerful_strike", 0)
        enemy = Enemy(
            "Бронированный враг", 100, 1, 1, 0,
            Damage_type.PHYSICAL, armor=3,
        )
        state = PlayerTurnState(
            {ATTACK_ACTION_KIND, ABILITY_ACTION_KIND}, action_points=3
        )

        with patch.object(player, "attack", return_value=(10, False)):
            result = use_ability_action(
                player, enemy, "powerful_strike", state
            )

        self.assertTrue(result.success)
        self.assertEqual(enemy.health, 83)
        self.assertEqual(state.action_points, 0)
        self.assertTrue(player.abilities.is_on_cooldown("powerful_strike"))
        self.assertIn("17 урона", result.messages[0])

    def test_fortify_uses_effect_system_and_expires_next_player_turn(self):
        player = self.make_bruiser()
        player.armor = Armor("Тестовый доспех", 10)
        player.equip_ability("fortify", 0)
        enemy = Enemy("Враг", 100, 1, 1, 0, Damage_type.PHYSICAL)
        state = PlayerTurnState({ABILITY_ACTION_KIND}, action_points=3)

        result = use_ability_action(player, enemy, "fortify", state)

        self.assertTrue(result.success)
        self.assertEqual(player.get_armor_defense(), 20)
        player.health = player.max_health
        self.assertEqual(player.take_damage(30, Damage_type.PHYSICAL), 10)
        player.health = player.max_health
        self.assertEqual(player.take_damage(30, Damage_type.ASTRAL), 30)
        player.trigger_turn_start_effects()
        self.assertEqual(player.get_armor_defense(), 10)

    def test_cooldown_two_blocks_exactly_the_next_two_player_turns(self):
        player = self.make_bruiser()
        player.equip_ability("fortify", 0)
        enemy = Enemy("Враг", 100, 1, 1, 0, Damage_type.PHYSICAL)
        state = PlayerTurnState({ABILITY_ACTION_KIND}, action_points=3)
        self.assertTrue(
            use_ability_action(player, enemy, "fortify", state).success
        )

        player.trigger_action_effects(NON_ATTACK_ACTION)
        player.trigger_action_effects(NON_ATTACK_ACTION)
        self.assertEqual(player.abilities.cooldown_remaining("fortify"), 2)

        player.start_ability_turn()  # turn 2
        self.assertTrue(player.abilities.is_on_cooldown("fortify"))
        player.start_ability_turn()  # turn 3
        self.assertTrue(player.abilities.is_on_cooldown("fortify"))
        player.start_ability_turn()  # turn 4
        self.assertFalse(player.abilities.is_on_cooldown("fortify"))

    def test_unavailable_ability_never_spends_action_points(self):
        player = self.make_bruiser()
        enemy = Enemy("Враг", 100, 1, 1, 0, Damage_type.PHYSICAL)
        state = PlayerTurnState({ABILITY_ACTION_KIND}, action_points=3)
        result = use_ability_action(player, enemy, "fortify", state)
        self.assertFalse(result.success)
        self.assertEqual(state.action_points, 3)

        player.equip_ability("fortify", 0)
        state.action_points = 2
        result = use_ability_action(player, enemy, "fortify", state)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "Недостаточно ОД.")
        self.assertEqual(state.action_points, 2)
        self.assertFalse(player.abilities.is_on_cooldown("fortify"))

    def test_snapshot_contains_three_slots_cost_and_cooldown(self):
        player = self.make_bruiser()
        player.equip_ability("powerful_strike", 0)
        snapshot = ability_snapshot(player)
        self.assertEqual(len(snapshot["slots"]), 3)
        entry = snapshot["slots"][0]
        self.assertEqual(entry["action_point_cost"], 3)
        self.assertEqual(entry["cooldown"], 2)
        self.assertTrue(entry["equipped"])

    def test_equipped_slots_are_direct_combat_actions_without_submenu(self):
        player = self.make_bruiser()
        player.equip_ability("powerful_strike", 0)
        enemy = Enemy("Враг", 100, 1, 1, 0, Damage_type.PHYSICAL)
        state = PlayerTurnState(
            {ATTACK_ACTION_KIND, ABILITY_ACTION_KIND}, action_points=3
        )
        self.assertIn(
            "5 - [1] Мощный удар — 3 ОД",
            get_player_turn_actions(state, player, enemy),
        )
        with patch("battle.input", return_value="5"), patch.object(
            player, "attack", return_value=(10, False)
        ):
            messages = player_turn(player, enemy, turn_state=state)
        self.assertIn("20 урона", messages[0])
        self.assertEqual(state.action_points, 0)


if __name__ == "__main__":
    unittest.main()
