import unittest
from unittest.mock import patch

from battle import (
    ATTACK_ACTION_KIND,
    CONSUMABLE_ACTION_KIND,
    MAGIC_ACTION_KIND,
    PlayerTurnState,
    cast_spell_action,
    create_player_turn_state,
    get_combat_spell_options,
    get_player_turn_actions,
    player_turn,
    should_end_player_turn,
)
from damage import Damage_type
from effects import NON_ATTACK_ACTION, PhysicalShield, Stun
from encounter import create_enemy
from enemy import Enemy
from objects import create_item
from player import Player
from spells import SPELLS


class TestEnemyArmor(unittest.TestCase):
    def test_enemy_armor_only_reduces_physical_damage(self):
        enemy = Enemy("Armored", 50, 1, 1, 0, Damage_type.PHYSICAL, armor=4)
        self.assertEqual(enemy.take_damage(10, Damage_type.PHYSICAL), 6)
        self.assertEqual(enemy.take_damage(10, Damage_type.ASTRAL), 10)

    def test_beasts_and_likho_have_no_armor(self):
        for enemy_id in ("wolf", "rat", "spider", "likho"):
            self.assertEqual(create_enemy(enemy_id, 1).armor, 0, enemy_id)

    def test_humanoid_enemy_has_armor(self):
        self.assertGreater(create_enemy("goblin", 1).armor, 0)


class TestActionPoints(unittest.TestCase):
    def setUp(self):
        self.player = Player("Hero", None)
        self.enemy = Enemy("Enemy", 100, 1, 1, 0, Damage_type.PHYSICAL)

    def test_attack_then_potion_uses_all_three_points(self):
        self.player.health = 20
        state = create_player_turn_state(self.player)
        with patch("battle.input", return_value="1"), patch.object(
                self.player, "attack", return_value=(5, False)):
            player_turn(self.player, self.enemy, turn_state=state)
        with patch("battle.input", side_effect=["3", "1"]), patch(
                "battle.show_battle_screen"):
            player_turn(self.player, self.enemy, turn_state=state)
        self.assertEqual(state.action_points, 0)
        self.assertFalse(state.can_use(ATTACK_ACTION_KIND))
        self.assertFalse(state.can_use(CONSUMABLE_ACTION_KIND))

    def test_action_labels_show_cost_and_unaffordable_actions_are_omitted(self):
        state = PlayerTurnState({ATTACK_ACTION_KIND, CONSUMABLE_ACTION_KIND}, action_points=1)
        actions = get_player_turn_actions(state)
        self.assertFalse(any("Атака" in action for action in actions))
        self.assertIn("3 - Использовать флягу — 1 ОД", actions)

    def test_spell_option_requires_both_action_points_and_mana(self):
        self.player.learn_spell(SPELLS["stun"])
        state = PlayerTurnState({MAGIC_ACTION_KIND}, action_points=0)
        option = next(iter(get_combat_spell_options(self.player, self.enemy, state).values()))
        self.assertFalse(option["enabled"])
        self.assertEqual(option["reason"], "Недостаточно ОД.")
        state.action_points = 3
        self.player.mana = 0
        option = next(iter(get_combat_spell_options(self.player, self.enemy, state).values()))
        self.assertFalse(option["enabled"])
        self.assertEqual(option["reason"], "Недостаточно MP.")

    def test_flasks_keep_the_player_turn_while_an_action_is_affordable(self):
        for resource in ("hp", "mp"):
            with self.subTest(resource=resource):
                player = Player("Hero", None)
                enemy = Enemy("Enemy", 100, 1, 1, 0, Damage_type.PHYSICAL)
                if resource == "hp":
                    player.health -= 10
                else:
                    player.mana = 0
                state = create_player_turn_state(player)

                with patch("battle.input", return_value=f"flask:{resource}"):
                    result = player_turn(player, enemy, turn_state=state)

                self.assertTrue(result)
                self.assertEqual(state.action_points, 2)
                self.assertFalse(state.is_complete)
                self.assertFalse(should_end_player_turn(player, enemy, state))

    def test_last_action_points_end_the_turn_automatically(self):
        state = PlayerTurnState({ATTACK_ACTION_KIND}, action_points=2)

        self.assertTrue(state.use(ATTACK_ACTION_KIND))
        self.assertTrue(should_end_player_turn(self.player, self.enemy, state))
        self.assertTrue(state.is_complete)


class TestNewCombatSpells(unittest.TestCase):
    def setUp(self):
        self.player = Player("Mage", None)
        self.enemy = Enemy("Enemy", 100, 1, 1, 0, Damage_type.PHYSICAL)

    def cast(self, spell_id, state=None):
        self.player.learn_spell(SPELLS[spell_id])
        state = state or PlayerTurnState({MAGIC_ACTION_KIND})
        target = self.player if SPELLS[spell_id].target == "self" else self.enemy
        return cast_spell_action(
            self.player, target, spell_id, state, action=NON_ATTACK_ACTION
        ), state

    def test_spell_submenu_back_adds_nothing_to_combat_log(self):
        self.player.learn_spell(SPELLS["healing"])
        state = PlayerTurnState({MAGIC_ACTION_KIND})
        with patch("battle.input", side_effect=("4", "0")), patch(
            "battle.show_battle_screen"
        ):
            messages = player_turn(
                self.player, self.enemy, messages=[], turn_state=state
            )
        self.assertEqual(messages, [])
        self.assertEqual(state.action_points, 3)

    def test_healing_caps_at_maximum(self):
        self.player.health = self.player.max_health - 5
        result, state = self.cast("healing")
        self.assertTrue(result.success)
        self.assertEqual(self.player.health, self.player.max_health)
        self.assertEqual(state.action_points, 2)
        change = result.messages[1].health_changes[0]
        self.assertEqual(
            (change.before, change.after, change.amount, change.kind),
            (self.player.max_health - 5, self.player.max_health, 5, "healing"),
        )

    def test_slow_time_is_once_per_turn_and_bonus_is_state_local(self):
        result, state = self.cast("slow_time")
        self.assertTrue(result.success)
        self.assertEqual(state.action_points, 4)
        self.player.mana = self.player.max_mana
        second, _ = self.cast("slow_time", state)
        self.assertFalse(second.success)
        self.assertEqual(create_player_turn_state(self.player).action_points, 3)

    def test_magic_shield_reduces_only_physical_and_expires_next_turn(self):
        result, _ = self.cast("magic_shield")
        self.assertTrue(result.success)
        self.assertEqual(self.player.take_damage(10, Damage_type.PHYSICAL), 7)
        self.player.health = self.player.max_health
        self.assertEqual(self.player.take_damage(10, Damage_type.ASTRAL), 10)
        self.player.trigger_turn_start_effects()
        self.player.health = self.player.max_health
        self.assertEqual(self.player.take_damage(10, Damage_type.PHYSICAL), 10)

    def test_magic_shield_central_damage_rounding_and_no_double_reduction(self):
        cases = (
            (False, Damage_type.PHYSICAL, 10, 10),
            (True, Damage_type.PHYSICAL, 10, 7),
            (True, Damage_type.PHYSICAL, 11, 7),
            (True, Damage_type.ASTRAL, 10, 10),
        )
        for shielded, damage_type, incoming, expected in cases:
            with self.subTest(shielded=shielded, damage_type=damage_type,
                              incoming=incoming):
                player = Player("Target", None)
                if shielded:
                    player.add_effect(PhysicalShield())
                    player.add_effect(PhysicalShield())
                received = player.take_damage(incoming, damage_type)
                self.assertEqual(received, expected)
                self.assertIs(type(player.health), int)

    def test_shield_and_stun_do_not_stack(self):
        self.player.add_effect(PhysicalShield())
        self.player.add_effect(PhysicalShield())
        self.enemy.add_effect(Stun())
        self.enemy.add_effect(Stun())
        self.assertEqual(len(self.player.effects.effects), 1)
        self.assertEqual(len(self.enemy.effects.effects), 1)
        self.assertTrue(self.enemy.trigger_turn_start_effects().skip_turn)
        self.assertFalse(self.enemy.trigger_turn_start_effects().skip_turn)

    def test_spells_keep_the_player_turn_while_an_action_is_affordable(self):
        for spell_id, expected_action_points in (
            ("healing", 2),
            ("slow_time", 4),
            ("magic_shield", 2),
            ("stun", 2),
        ):
            with self.subTest(spell_id=spell_id):
                self.setUp()
                if spell_id == "healing":
                    self.player.health -= 10
                state = PlayerTurnState(
                    {ATTACK_ACTION_KIND, MAGIC_ACTION_KIND}
                )

                result, state = self.cast(spell_id, state)

                self.assertTrue(result.success)
                self.assertEqual(state.action_points, expected_action_points)
                self.assertFalse(state.is_complete)
                self.assertFalse(
                    should_end_player_turn(self.player, self.enemy, state)
                )


if __name__ == "__main__":
    unittest.main()
