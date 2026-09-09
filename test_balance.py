import unittest

from character_class import CLASSES
from damage import Damage_type
from objects import ENEMIES, ITEMS, STARTER_WEAPON, WEAPONS
from player import Player


class TestScaledBalance(unittest.TestCase):
    def test_class_health_values(self):
        self.assertEqual(CLASSES["bruiser"].max_health, 120)
        self.assertEqual(CLASSES["daredevil"].max_health, 105)
        self.assertEqual(CLASSES["herald"].max_health, 85)

    def test_default_player_and_unarmed_damage_use_new_scale(self):
        player = Player("Герой", None)

        self.assertEqual((player.health, player.max_health), (120, 120))
        self.assertEqual(player.attack(), (12, False))

    def test_starter_weapon_uses_new_scale(self):
        self.assertEqual(
            (STARTER_WEAPON.min_damage, STARTER_WEAPON.max_damage),
            (10, 18),
        )

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
            "goblin": (100, 8, 16),
            "wolf": (90, 8, 12),
            "rat": (70, 8, 10),
            "spider": (80, 10, 16),
            "skeleton": (120, 12, 18),
            "demon": (180, 28, 48),
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


if __name__ == "__main__":
    unittest.main()
