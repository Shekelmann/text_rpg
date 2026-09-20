import random
import unittest
from copy import deepcopy

from affix import AFFIX_COUNTS
from affix_pool import (
    ARMOR_BREAK, ARMOR_PENETRATION, ASTRAL_DAMAGE, DRAIN,
    WEAPON_AFFIX_POOLS, reroll_weapon_affixes,
)
from character_class import CLASSES
from combat_hit import resolve_hit
from damage import Damage_type
from effects import ArmorBreak, Drain
from enemy import Enemy
from gui_views import enemy_effects_snapshot
from objects import (
    CLASS_STARTING_WEAPON_POOLS, ITEMS, WEAPONS,
    generate_starting_weapons,
)
from player import Player
from rarity import Rarity


class TestWeaponAffixRules(unittest.TestCase):
    def test_fixed_counts_and_weapon_specific_generation(self):
        expected = {
            Rarity.COMMON: 0,
            Rarity.RARE: 1,
            Rarity.EPIC: 2,
        }
        self.assertEqual(
            {rarity: bounds[0] for rarity, bounds in AFFIX_COUNTS.items()},
            expected,
        )
        self.assertTrue(all(low == high for low, high in AFFIX_COUNTS.values()))

        for weapon_id, pool in WEAPON_AFFIX_POOLS.items():
            for rarity, count in expected.items():
                weapon = deepcopy(WEAPONS[weapon_id])
                weapon.rarity = rarity
                reroll_weapon_affixes(weapon, random.Random(7))
                self.assertEqual(len(weapon.affixes), count)
                self.assertTrue(all(affix in pool for affix in weapon.affixes))

        rare_sword = deepcopy(WEAPONS["sword"])
        rare_sword.rarity = Rarity.RARE
        with self.assertRaises(ValueError):
            rare_sword.set_affixes(())

    def test_reroll_uses_the_same_pool(self):
        for weapon_id, pool in WEAPON_AFFIX_POOLS.items():
            weapon = deepcopy(WEAPONS[weapon_id])
            weapon.rarity = Rarity.RARE
            for seed in range(10):
                weapon.reroll_affixes(random.Random(seed))
                self.assertIn(weapon.affixes[0], pool)

    def test_two_handed_mace_and_only_one_handed_staff_remain(self):
        self.assertEqual(WEAPONS["club"].weapon_type, "Двуручное")
        self.assertEqual(WEAPONS["staff"].weapon_type, "Одноручное")
        self.assertNotIn("staff_2h", WEAPONS)
        self.assertNotIn("2 handed staff", ITEMS)

    def test_armor_penetration_is_local_to_one_hit(self):
        enemy = Enemy("Цель", 100, 1, 1, 0, Damage_type.PHYSICAL, armor=10)
        axe = deepcopy(WEAPONS["axe_2h"])
        axe.rarity = Rarity.RARE
        axe.set_affixes((ARMOR_PENETRATION,))

        first = resolve_hit(
            enemy, lambda: (20, False), Damage_type.PHYSICAL,
            armor_penetration=axe.armor_penetration,
        )
        second = resolve_hit(enemy, lambda: (20, False), Damage_type.PHYSICAL)

        self.assertEqual((first.damage, second.damage), (13, 10))
        self.assertEqual(enemy.armor, 10)

    def test_armor_break_refreshes_without_stacking(self):
        enemy = Enemy("Цель", 100, 1, 1, 0, Damage_type.PHYSICAL, armor=10)
        mace = deepcopy(WEAPONS["club"])
        mace.rarity = Rarity.RARE
        mace.set_affixes((ARMOR_BREAK,))

        mace.on_hit(enemy)
        effect = enemy.effects.get("armor_break")
        self.assertIsInstance(effect, ArmorBreak)
        self.assertEqual(enemy.get_armor_defense(), 7)
        effect.turns_remaining = 1
        mace.on_hit(enemy)
        self.assertIs(enemy.effects.get("armor_break"), effect)
        self.assertEqual(effect.turns_remaining, 2)
        self.assertEqual(len(enemy.effects.active), 1)
        self.assertEqual(enemy.armor, 10)
        snapshot = enemy_effects_snapshot(enemy)[0]
        self.assertEqual(snapshot["tooltip"][0], "Слом брони")
        self.assertIn("30%", snapshot["tooltip"][1])

    def test_staff_astral_damage_and_existing_drain_effect(self):
        staff = deepcopy(WEAPONS["staff"])
        staff.rarity = Rarity.EPIC
        staff.set_affixes((ASTRAL_DAMAGE, DRAIN))
        player = Player("Герой", staff)
        enemy = Enemy("Цель", 100, 1, 1, 0, Damage_type.PHYSICAL)

        self.assertEqual(staff.get_damage_range(), (14, 28))
        staff.on_hit(enemy, source=player)
        drain = enemy.effects.get("drain")
        self.assertIsInstance(drain, Drain)
        self.assertIs(drain.source, player)

    def test_starting_weapons_use_requested_class_pools(self):
        self.assertEqual(CLASS_STARTING_WEAPON_POOLS["bruiser"],
                         ("club", "axe_2h", "sword"))
        self.assertEqual(CLASS_STARTING_WEAPON_POOLS["daredevil"],
                         ("sword", "dagger", "dagger"))
        self.assertEqual(CLASS_STARTING_WEAPON_POOLS["herald"],
                         ("staff", "sword", "axe"))
        for class_id, character_class in CLASSES.items():
            weapons = generate_starting_weapons(character_class, random.Random(9))
            self.assertEqual(len(weapons), 3)
            self.assertTrue(all(
                weapon.icon_id in CLASS_STARTING_WEAPON_POOLS[class_id]
                for weapon in weapons
            ))


if __name__ == "__main__":
    unittest.main()
