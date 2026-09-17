import unittest

from character_class import CLASSES
from damage import Damage_type
from objects import ENEMIES, ITEMS, WEAPONS
from player import Player
from balance_report import (
    row, expected_actions, reference_player, player_distribution,
    enemy_distribution, successful_distribution, opening_spell_rounds,
)
from encounter import create_enemy
from spells import SPELLS


class TestScaledBalance(unittest.TestCase):
    def test_class_health_values(self):
        self.assertEqual(CLASSES["bruiser"].max_health, 105)
        self.assertEqual(CLASSES["daredevil"].max_health, 100)
        self.assertEqual(CLASSES["herald"].max_health, 95)

    def test_default_player_and_unarmed_damage_use_new_scale(self):
        player = Player("Герой", None)

        self.assertEqual((player.health, player.max_health), (120, 120))
        self.assertEqual(player.attack(), (12, False))

    def test_weapon_catalog_uses_scaled_damage(self):
        expected_ranges = {
            "sword": (12, 28),
            "axe": (16, 36),
            "axe_2h": (40, 76),
            "dagger": (4, 20),
            "club": (40, 48),
            "staff": (10, 24),
            "staff_2h": (28, 52),
        }

        for weapon_id, damage_range in expected_ranges.items():
            with self.subTest(weapon=weapon_id):
                weapon = WEAPONS[weapon_id]
                self.assertEqual(weapon.level, 1)
                self.assertEqual(
                    (weapon.min_damage, weapon.max_damage),
                    damage_range,
                )

    def test_removed_weapon_types_are_absent(self):
        self.assertNotIn("sword_2h", WEAPONS)
        self.assertNotIn("spear", WEAPONS)
        self.assertNotIn("club_2h", WEAPONS)
        self.assertNotIn("2 handed sword", ITEMS)

    def test_staves_deal_astral_damage(self):
        self.assertIs(WEAPONS["staff"].damage_type, Damage_type.ASTRAL)
        self.assertIs(WEAPONS["staff_2h"].damage_type, Damage_type.ASTRAL)

    def test_enemy_catalog_uses_scaled_health_and_damage(self):
        expected_values = {
            "goblin": (160, 7, 11),
            "wolf": (145, 6, 10),
            "rat": (105, 4, 7),
            "spider": (130, 5, 9),
            "skeleton": (170, 7, 11),
            "demon": (300, 16, 22),
        }

        for enemy_id, values in expected_values.items():
            with self.subTest(enemy=enemy_id):
                enemy = ENEMIES[enemy_id]
                self.assertEqual(
                    (enemy["health"], enemy["min_damage"], enemy["max_damage"]),
                    values,
                )

    def test_healing_item_remains_proportional_to_health_scale(self):
        self.assertEqual(ITEMS["heal"].heal, 40)

    def test_level_up_health_uses_new_scale(self):
        player = Player("Герой", None)
        player.level_up()

        self.assertEqual(player.max_health, 132)
        self.assertEqual(player.health, 132)


class TestReferenceTTK(unittest.TestCase):
    def test_discrete_ttk_counts_overkill_and_misses(self):
        self.assertEqual(expected_actions(11, {10: 1}), 2)
        self.assertEqual(expected_actions(11, {0: .5, 10: .5}), 4)
        self.assertAlmostEqual(expected_actions(15, {10: .5, 20: .5}), 1.5)

    def test_equal_goblin_takes_six_to_eight_successful_attacks_for_all_classes(self):
        for class_id in CLASSES:
            for level in (1, 3, 6, 10):
                with self.subTest(class_id=class_id, level=level):
                    result = row("goblin", level, class_id)
                    self.assertGreaterEqual(result["player_ttk_hits"], 6)
                    self.assertLessEqual(result["player_ttk_hits"], 8)
                    self.assertGreater(result["enemy_ttk_attempts"], result["player_ttk_attempts"])

    def test_early_enemies_do_not_outrace_unarmored_reference_heroes_on_average(self):
        for class_id in CLASSES:
            for enemy_id in ("goblin", "wolf", "likho", "leshy", "spider", "mutant", "skeleton"):
                for level in (1, 2, 3):
                    with self.subTest(class_id=class_id, enemy=enemy_id, level=level):
                        result = row(enemy_id, level, class_id, armor=0)
                        self.assertGreater(result["enemy_ttk_attempts"], result["player_ttk_attempts"])

    def test_dodge_changes_attempts_not_successful_hit_damage(self):
        result = row("wolf")
        self.assertAlmostEqual(result["player_ttk_attempts"], result["player_ttk_hits"] / .88)
        self.assertAlmostEqual(result["enemy_ttk_attempts"], result["enemy_ttk_hits"] / .99)

    def test_dangerous_and_elite_remain_harder_than_common(self):
        common = row("goblin", 3)
        dangerous = row("goblin", 3, rarity="dangerous")
        elite = row("goblin", 3, rarity="elite")
        self.assertLess(common["player_ttk_hits"], dangerous["player_ttk_hits"])
        self.assertLess(dangerous["player_ttk_hits"], elite["player_ttk_hits"])
        self.assertGreater(common["enemy_ttk_hits"], elite["enemy_ttk_hits"])

    def test_astral_staff_uses_int_and_ignores_strength(self):
        player = reference_player("herald", 3)
        enemy = create_enemy("goblin", 3)
        original = player_distribution(player, enemy)
        player.strength += 50
        self.assertEqual(original, player_distribution(player, enemy))
        player.intelligence += 2
        self.assertNotEqual(original, player_distribution(player, enemy))

    def test_healing_spell_is_limited_by_actual_mana(self):
        player = reference_player("herald")
        spell = SPELLS["healing"]
        player.health = 1
        casts = player.mana // spell.cost
        self.assertEqual(casts, 2)
        for _ in range(casts):
            result = player.cast_spell(spell.id, player)
            self.assertTrue(result.success)
        self.assertEqual(player.health, 41)
        self.assertFalse(player.cast_spell(spell.id, player).success)

    def test_armor_changes_physical_incoming_distribution_only(self):
        armored = reference_player()
        unarmored = reference_player(armor=0)
        physical = create_enemy("goblin", 1)
        astral = create_enemy("likho", 1)
        self.assertNotEqual(enemy_distribution(physical, armored), enemy_distribution(physical, unarmored))
        self.assertEqual(enemy_distribution(astral, armored), enemy_distribution(astral, unarmored))


if __name__ == "__main__":
    unittest.main()
