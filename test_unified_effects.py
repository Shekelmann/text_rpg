import unittest
from unittest.mock import patch

from battle import (battle, cast_spell_action, create_player_turn_state,
                    PlayerTurnState, MAGIC_ACTION_KIND)
from damage import Damage_type
from effects import (ATTACK_ACTION, NON_ATTACK_ACTION, Bleeding, Drain,
                     EffectType, GainActionPoint, Heal, PhysicalShield,
                     Poison, Stun)
from enemy import Enemy
from gui_views import effects_snapshot, enemy_combat_snapshot
from intent import EnemyIntent
from player import Player
from spell import Spell
from spells import SPELLS


def actors():
    return Player("Hero", None), Enemy("Enemy", 100, 1, 1, 0, Damage_type.PHYSICAL)


class TestUnifiedEffects(unittest.TestCase):
    def test_instant_heal_on_both_actors_caps_and_keeps_feedback(self):
        for actor in actors():
            with self.subTest(actor=actor.name):
                actor.health -= 3
                result = actor.apply_effect(Heal(20))
                self.assertEqual(result.health_restored, 3)
                self.assertEqual(actor.health, actor.max_health)
                self.assertEqual(result.messages[0].health_changes[0].amount, 3)
                self.assertEqual(effects_snapshot(actor), ())

    def test_action_points_are_a_transient_result_for_either_actor(self):
        for actor in actors():
            result = actor.apply_effect(GainActionPoint())
            self.assertEqual(result.action_points_gain, 1)
            self.assertEqual(actor.effects.active, ())

    def test_custom_spell_grants_ap_through_effect_result(self):
        player, enemy = actors()
        spell = Spell("ap_test", "Test", target="self", action_cost=0,
                      effects=(GainActionPoint(),))
        player.learn_spell(spell)
        state = PlayerTurnState({MAGIC_ACTION_KIND})
        result = cast_spell_action(player, enemy, spell.id, state, action=NON_ATTACK_ACTION)
        self.assertTrue(result.success)
        self.assertEqual(state.action_points, 4)
        self.assertEqual(create_player_turn_state(player).action_points, 3)
        self.assertFalse(player.effects.active)

    def test_existing_spell_content_uses_effects(self):
        self.assertIsInstance(SPELLS["healing"].effects[0], Heal)
        self.assertIsInstance(SPELLS["slow_time"].effects[0], GainActionPoint)

    def test_legacy_spell_fields_still_resolve_via_effects(self):
        player, _ = actors()
        player.health -= 10
        spell = Spell("legacy", "Legacy", target="self", healing=4, action_points_gain=1)
        result = spell.apply(player, player)
        self.assertEqual(player.health, player.max_health - 6)
        self.assertEqual(result.action_points_gain, 1)
        self.assertFalse(player.effects.active)

    def test_shared_shield_damage_expiry_and_nonstacking(self):
        for actor in actors():
            with self.subTest(actor=actor.name):
                actor.apply_effect(PhysicalShield())
                actor.apply_effect(PhysicalShield())
                self.assertEqual(len(actor.effects.active), 1)
                self.assertEqual(actor.take_damage(10, Damage_type.PHYSICAL), 7)
                self.assertEqual(actor.take_damage(10, Damage_type.ASTRAL), 10)
                self.assertEqual(actor.take_damage(10, bypass_mitigation=True), 10)
                actor.trigger_turn_end_effects()
                self.assertIsNotNone(actor.effects.get("magic_shield"))
                actor.trigger_turn_start_effects()
                self.assertIsNone(actor.effects.get("magic_shield"))

    def test_enemy_shield_precedes_armor(self):
        _, enemy = actors()
        enemy.armor = 4
        enemy.apply_effect(PhysicalShield())
        self.assertEqual(enemy.take_damage(20, Damage_type.PHYSICAL), 10)

    def test_both_actors_share_poison_bleeding_and_skip_policies(self):
        for actor in actors():
            actor.apply_effect(Poison(2))
            actor.apply_effect(Poison(1))
            actor.apply_effect(Bleeding(2, 2))
            actor.apply_effect(Stun())
            actor.apply_effect(Stun())
            start = actor.trigger_turn_start_effects()
            self.assertEqual(start.damage, 3)
            self.assertTrue(start.skip_turn)
            self.assertEqual(actor.trigger_turn_end_effects().damage, 0)
            self.assertEqual(actor.trigger_action_effects(NON_ATTACK_ACTION).damage, 0)
            self.assertEqual(actor.trigger_action_effects(ATTACK_ACTION).damage, 2)
            self.assertEqual(actor.trigger_action_effects(ATTACK_ACTION).damage, 2)
            self.assertIsNone(actor.effects.get("bleeding"))
            self.assertFalse(actor.trigger_turn_start_effects().skip_turn)
            self.assertEqual(actor.trigger_turn_start_effects().damage, 1)
            self.assertFalse(actor.effects.active)

    def test_drain_can_have_enemy_source_without_inventing_mana(self):
        player, enemy = actors()
        enemy.health = 40
        player.apply_effect(Drain(4, enemy))
        for _ in range(2):
            result = player.trigger_turn_start_effects()
            self.assertEqual((result.damage, result.health_restored, result.mana_restored), (4, 2, 0))
        self.assertEqual(enemy.health, 44)
        self.assertFalse(player.effects.active)
        self.assertFalse(hasattr(enemy, "mana"))

    def test_remove_exact_bleed_and_ignore_expired_poison_when_reapplying(self):
        player, _ = actors()
        first = player.add_effect(Bleeding(2, 2))
        second = player.add_effect(Bleeding(3, 2))
        self.assertTrue(player.effects.remove(first))
        self.assertFalse(player.effects.remove(first))
        self.assertIs(player.effects.get("bleeding"), second)
        expired = player.add_effect(Poison(0))
        fresh = player.add_effect(Poison(3))
        self.assertIsNot(expired, fresh)
        self.assertEqual(player.effects.get("poison").value, 3)

    def test_presentation_shared_and_intent_independent(self):
        player, enemy = actors()
        for actor in (player, enemy):
            actor.apply_effect(Poison(3))
            actor.apply_effect(PhysicalShield())
        self.assertEqual(effects_snapshot(player), effects_snapshot(enemy))
        entries = effects_snapshot(player)
        self.assertEqual([entry["effect_type"] for entry in entries], ["debuff", "buff"])
        self.assertIn("Сила: 3", entries[0]["tooltip"])
        enemy.intent = EnemyIntent.DEBUFF
        before = enemy_combat_snapshot(enemy)["enemy_intent"]
        enemy.apply_effect(Stun())
        self.assertEqual(before, enemy_combat_snapshot(enemy)["enemy_intent"])
        self.assertEqual(Heal.effect_type, EffectType.BUFF)

    def test_player_stun_skips_real_battle_turn_but_dots_still_tick(self):
        player, enemy = actors()
        player.apply_effect(Stun())
        player.apply_effect(Poison(2))
        enemy.apply_effect(Poison(100))
        with patch("battle.player_turn") as action, patch("battle.show_messages"), \
                patch("battle.show_battle_screen"), patch("battle.finish_victory", return_value=True):
            self.assertTrue(battle(player, enemy))
        action.assert_not_called()
        self.assertEqual(player.health, player.max_health - 2)
        self.assertIsNone(player.effects.get("skip_turn"))


if __name__ == "__main__":
    unittest.main()
