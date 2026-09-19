import pickle
import unittest
from unittest.mock import patch

from battle import enemy_turn
from encounter import create_enemy
from intent import EnemyIntent, intent_presentation
from objects import ENEMIES
from player import Player


class TestEnemyIntent(unittest.TestCase):
    def test_four_base_categories_have_required_presentations(self):
        self.assertEqual(
            {intent.value for intent in EnemyIntent},
            {"physical_attack", "astral_attack", "buff", "debuff"},
        )
        expected = {
            EnemyIntent.PHYSICAL_ATTACK: (
                "Физическая атака",
                "Враг собирается совершить физическую атаку.",
            ),
            EnemyIntent.ASTRAL_ATTACK: (
                "Астральная атака",
                "Враг собирается совершить астральную атаку.",
            ),
            EnemyIntent.BUFF: (
                "Бафф",
                "Враг собирается усилить себя или союзника.",
            ),
            EnemyIntent.DEBUFF: (
                "Дебафф",
                "Враг собирается наложить отрицательный эффект.",
            ),
        }
        for intent, (title, description) in expected.items():
            presentation = intent_presentation(intent)
            self.assertEqual((presentation["title"], presentation["description"]),
                             (title, description))
            self.assertTrue(presentation["icon"])

    def test_every_existing_enemy_starts_with_physical_attack(self):
        for enemy_id in ENEMIES:
            with self.subTest(enemy=enemy_id):
                enemy = create_enemy(enemy_id, 1)
                self.assertIs(enemy.intent, EnemyIntent.PHYSICAL_ATTACK)
                self.assertEqual(enemy.get_available_intents(),
                                 (EnemyIntent.PHYSICAL_ATTACK,))

    def test_intent_is_owned_by_each_enemy(self):
        first = create_enemy("goblin", 1)
        second = create_enemy("wolf", 1)
        first.intent = EnemyIntent.BUFF
        self.assertIs(first.intent, EnemyIntent.BUFF)
        self.assertIs(second.intent, EnemyIntent.PHYSICAL_ATTACK)

    def test_enemy_prepares_next_intent_after_acting(self):
        enemy = create_enemy("goblin", 1)
        player = Player("Hero", None)
        with patch.object(enemy, "attack", return_value=(1, False)), \
                patch.object(enemy, "prepare_next_intent",
                             wraps=enemy.prepare_next_intent) as prepare:
            enemy_turn(enemy, player)
        prepare.assert_called_once_with()
        self.assertIs(enemy.intent, EnemyIntent.PHYSICAL_ATTACK)

    def test_old_pickled_enemy_gets_default_intent(self):
        enemy = create_enemy("goblin", 1)
        del enemy.intent
        restored = pickle.loads(pickle.dumps(enemy))
        self.assertIs(restored.intent, EnemyIntent.PHYSICAL_ATTACK)


if __name__ == "__main__":
    unittest.main()
