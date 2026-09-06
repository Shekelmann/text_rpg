import unittest
from unittest.mock import patch

from battle import battle, enemy_turn
from damage import Damage_type
from effects import ATTACK_ACTION, Bleeding, CombatAction, Drain, Poison
from enemy import Enemy
from player import Player


def make_target(health=100):
    return Enemy("Target", health, 0, 0, 0, Damage_type.PHYSICAL)


class TestPoison(unittest.TestCase):
    def test_poison_six_deals_decreasing_damage_and_is_removed(self):
        target = make_target()
        target.add_effect(Poison(6))

        damages = [
            target.trigger_turn_start_effects().damage
            for _ in range(6)
        ]

        self.assertEqual(damages, [6, 5, 4, 3, 2, 1])
        self.assertEqual(target.health, 79)
        self.assertFalse(target.effects.contains(Poison))

    def test_poison_application_adds_to_existing_stack(self):
        target = make_target()
        poison = target.add_effect(Poison(5))

        stacked = target.add_effect(Poison(3))

        self.assertIs(stacked, poison)
        self.assertEqual(poison.value, 8)
        self.assertEqual(len(target.effects.effects), 1)

    def test_poison_message_names_enemy_target(self):
        target = Enemy("Гоблин", 10, 0, 0, 0, Damage_type.PHYSICAL)
        target.add_effect(Poison(2))

        result = target.trigger_turn_start_effects()

        self.assertEqual(
            result.messages,
            ["Яд наносит противнику «Гоблин» 2 урона."],
        )

    def test_poison_message_addresses_player(self):
        target = Player("Hero", None)
        target.add_effect(Poison(2))

        result = target.trigger_turn_start_effects()

        self.assertEqual(result.messages, ["Яд наносит вам 2 урона."])

    def test_astral_poison_uses_matching_resistance(self):
        target = Player("Hero", None)
        target.set_resistance(Damage_type.ASTRAL, 0.20)
        target.add_effect(Poison(10, Damage_type.ASTRAL))

        result = target.trigger_turn_start_effects()

        self.assertEqual(result.damage, 8)
        self.assertEqual(target.health, target.max_health - 8)

    def test_typed_poison_stacks_separately_by_damage_type(self):
        target = Player("Hero", None)
        astral = target.add_effect(Poison(3, Damage_type.ASTRAL))
        elemental = target.add_effect(Poison(4, Damage_type.ELEMENTAL))

        self.assertIsNot(astral, elemental)
        self.assertEqual(len(target.effects.effects), 2)


class TestBleeding(unittest.TestCase):
    def test_bleeding_triggers_on_attack_action(self):
        target = make_target()
        bleeding = target.add_effect(Bleeding(damage=4, triggers=3))

        result = target.trigger_action_effects(ATTACK_ACTION)

        self.assertEqual(result.damage, 4)
        self.assertEqual(target.health, 96)
        self.assertEqual(bleeding.triggers, 2)

    def test_bleeding_ignores_non_attack_action_without_losing_trigger(self):
        target = make_target()
        bleeding = target.add_effect(Bleeding(damage=4, triggers=3))
        healing_action = CombatAction("heal", is_attack=False)

        result = target.trigger_action_effects(healing_action)

        self.assertEqual(result.damage, 0)
        self.assertEqual(target.health, 100)
        self.assertEqual(bleeding.triggers, 3)

    def test_bleeding_is_removed_after_last_trigger(self):
        target = make_target()
        target.add_effect(Bleeding(damage=4, triggers=1))

        target.trigger_action_effects(ATTACK_ACTION)

        self.assertEqual(target.health, 96)
        self.assertFalse(target.effects.contains(Bleeding))

    def test_elemental_bleeding_uses_matching_resistance(self):
        target = Player("Hero", None)
        target.set_resistance(Damage_type.ELEMENTAL, 0.50)
        target.add_effect(
            Bleeding(10, triggers=1, damage_type=Damage_type.ELEMENTAL)
        )

        result = target.trigger_action_effects(ATTACK_ACTION)

        self.assertEqual(result.damage, 5)
        self.assertEqual(target.health, target.max_health - 5)

    def test_enemy_attack_notifies_bleeding_through_combat_action(self):
        player = Player("Hero", None)
        enemy = make_target()
        enemy.add_effect(Bleeding(damage=4, triggers=1))

        with patch.object(enemy, "attack", return_value=1), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(enemy.health, 96)
        self.assertIn(
            "Кровотечение наносит противнику «Target» 4 урона.",
            messages,
        )


class TestEffectCombatEvents(unittest.TestCase):
    @patch("battle.generate_loot", return_value=[])
    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_poison_triggers_at_enemy_turn_start(
        self,
        _mock_screen,
        _mock_sleep,
        _mock_loot,
    ):
        player = Player("Hero", None)
        enemy = make_target(health=3)
        enemy.add_effect(Poison(3))

        with patch("builtins.input", side_effect=["2", ""]):
            result = battle(player, enemy)

        self.assertTrue(result)
        self.assertEqual(enemy.health, 0)


class TestDrain(unittest.TestCase):
    def test_drain_four_deals_four_and_restores_two_health_and_mana(self):
        source = Player("Hero", None)
        source.health = 20
        source.mana = 5
        target = make_target()

        result = Drain(4).trigger(target, source)

        self.assertEqual(result.damage, 4)
        self.assertEqual(result.health_restored, 2)
        self.assertEqual(result.mana_restored, 2)
        self.assertEqual(target.health, 96)
        self.assertEqual(source.health, 22)
        self.assertEqual(source.mana, 7)
        self.assertEqual(
            result.messages,
            [
                "Иссушение наносит противнику «Target» 4 урона "
                "и восстанавливает 2 HP, 2 MP."
            ],
        )

    def test_drain_five_rounds_restoration_down(self):
        source = Player("Hero", None)
        source.health = 20
        source.mana = 5
        target = make_target()

        result = Drain(5).trigger(target, source)

        self.assertEqual(result.damage, 5)
        self.assertEqual(result.health_restored, 2)
        self.assertEqual(result.mana_restored, 2)
        self.assertEqual(target.health, 95)
        self.assertEqual(source.health, 22)
        self.assertEqual(source.mana, 7)

    def test_drain_restoration_does_not_exceed_resource_maximums(self):
        source = Player("Hero", None)
        source.health = source.max_health - 1
        source.mana = source.max_mana - 1
        target = make_target()

        result = Drain(7).trigger(target, source)

        self.assertEqual(source.health, source.max_health)
        self.assertEqual(source.mana, source.max_mana)
        self.assertEqual(result.health_restored, 1)
        self.assertEqual(result.mana_restored, 1)


if __name__ == "__main__":
    unittest.main()
