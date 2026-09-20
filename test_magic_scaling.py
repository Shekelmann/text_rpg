import unittest
from unittest.mock import patch

from battle import enemy_turn, show_messages
from character_class import CLASSES
from combat_feedback import feedback_message, mana_change
from damage import Damage_type
from encounter import create_enemy
from gui_views import spellbook_snapshot
from player import Player
from spells import SPELLS


class TestMagicScaling(unittest.TestCase):
    def test_class_base_mana_scales_with_intelligence(self):
        for class_id in ("bruiser", "daredevil", "herald"):
            with self.subTest(class_id=class_id):
                character_class = CLASSES[class_id]
                player = Player("Hero", None, character_class)
                self.assertEqual(
                    player.max_mana,
                    character_class.max_mana + character_class.intelligence,
                )
                self.assertEqual(player.mana, player.max_mana)

    def test_intelligence_allocation_recalculates_and_caps_mana(self):
        player = Player("Hero", None)
        player.mana = player.max_mana - 3
        player.unspent_stat_points = 1
        old_max = player.max_mana

        self.assertTrue(player.allocate_stat("intelligence"))
        self.assertEqual(player.max_mana, old_max + 1)
        self.assertEqual(player.mana, player.max_mana - 3)

        player.mana = 999
        player.recalculate_max_mana()
        self.assertLessEqual(player.mana, player.max_mana)

    def test_healing_uses_current_intelligence_and_caps_health(self):
        player = Player("Mage", None)
        player.intelligence = 5
        player.recalculate_max_mana(restore_to_full=True)
        player.learn_spell(SPELLS["healing"])
        player.health = player.max_health - 25

        result = player.cast_spell("healing", player)

        self.assertTrue(result.success)
        self.assertEqual(player.health, player.max_health - 5)
        self.assertTrue(any("20 HP" in message for message in result.messages))

    def test_shield_scales_with_int_and_caps_at_sixty_percent(self):
        cases = ((0, 8), (5, 7), (10, 6), (30, 4))
        for intelligence, expected in cases:
            with self.subTest(intelligence=intelligence):
                player = Player("Mage", None)
                player.intelligence = intelligence
                player.recalculate_max_mana(restore_to_full=True)
                player.learn_spell(SPELLS["magic_shield"])
                self.assertTrue(player.cast_spell("magic_shield", player).success)
                self.assertEqual(
                    player.take_damage(10, Damage_type.PHYSICAL), expected
                )
                player.health = player.max_health
                self.assertEqual(
                    player.take_damage(10, Damage_type.ASTRAL), 10
                )

    def test_shield_scales_each_physical_hit_exactly_once(self):
        player = Player("Mage", None)
        player.intelligence = 5
        player.recalculate_max_mana(restore_to_full=True)
        player.learn_spell(SPELLS["magic_shield"])
        player.cast_spell("magic_shield", player)

        received = tuple(
            player.take_damage(damage, Damage_type.PHYSICAL)
            for damage in (10, 20, 11)
        )

        self.assertEqual(received, (7, 14, 7))
        self.assertIs(type(player.health), int)

    def test_spellbook_shows_current_heal_and_shield_strength(self):
        player = Player("Mage", None)
        player.intelligence = 5
        player.learn_spell(SPELLS["healing"])
        player.learn_spell(SPELLS["magic_shield"])

        details = {
            entry["id"]: entry["details"]
            for entry in spellbook_snapshot(player)["learned"]
        }
        self.assertIn("сила: 20", details["healing"])
        self.assertIn("снижение физического урона: 30%", details["magic_shield"])

    def test_likho_astral_attack_bypasses_shield_and_is_logged(self):
        player = Player("Hero", None)
        player.intelligence = 10
        player.recalculate_max_mana(restore_to_full=True)
        player.learn_spell(SPELLS["magic_shield"])
        player.cast_spell("magic_shield", player)
        likho = create_enemy("likho", 1)

        with patch.object(likho, "attack", return_value=(10, False)), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(likho, player)

        self.assertEqual(player.max_health - player.health, 10)
        self.assertIn("10 Astral-урона", messages[0])
        self.assertEqual(messages[0].health_changes[0].damage_type, "ASTRAL")

    def test_mana_restore_feedback_reaches_battle_presentation(self):
        player = Player("Hero", None)
        enemy = create_enemy("goblin", 1)
        message = feedback_message(
            "Восстановлено 5 MP.",
            mana_change(player, 1, 6),
        )

        with patch("battle.show_battle_screen") as show, patch(
            "battle.time.sleep"
        ):
            show_messages(player, enemy, [], [message])

        resource = show.call_args.kwargs["resource_events"][0]
        self.assertEqual(
            (resource["resource"], resource["amount"], resource["target"]),
            ("mana", 5, "player"),
        )


if __name__ == "__main__":
    unittest.main()
