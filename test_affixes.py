import io
import random
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from affix import (
    Affix, AffixType, Modifier, ModifierOperation, apply_modifiers,
    generate_affixes,
)
from damage import Damage_type
from interface import format_item_for_menu, _show_weapon_details
from objects import ITEMS, create_item
from player import Player
from rarity import Rarity
from weapon import Weapon


# Temporary test values, not the game's affix pool or a tier progression.
TEST_POOL = (
    Affix("test_flat", "Пробный урон", AffixType.PREFIX, 1,
          (Modifier("physical_damage", ModifierOperation.FLAT, 5),)),
    Affix("test_crit", "Пробный крит", AffixType.PREFIX, 1,
          (Modifier("crit_chance", ModifierOperation.FLAT, 0.05),)),
    Affix("test_percent", "Пробный процент", AffixType.SUFFIX, 1,
          (Modifier("physical_damage", ModifierOperation.PERCENT, 20),)),
    Affix("test_crit_percent", "Пробный процент крита", AffixType.SUFFIX, 1,
          (Modifier("crit_chance", ModifierOperation.PERCENT, 50),)),
)


def weapon(affixes=(), **kwargs):
    kwargs.setdefault("rarity", Rarity.EPIC)
    return Weapon("Тест", 10, 10, 0.1, "Двуручное",
                  kwargs.pop("damage_type", Damage_type.PHYSICAL),
                  affixes=affixes, **kwargs)


class TestAffixStats(unittest.TestCase):
    def test_flat_then_summed_percent_is_order_independent(self):
        modifiers = [Modifier("physical_damage", operation, value) for operation, value in (
            (ModifierOperation.PERCENT, 20), (ModifierOperation.FLAT, 5),
            (ModifierOperation.PERCENT, 30), (ModifierOperation.FLAT, 5),
        )]
        self.assertEqual(apply_modifiers(10, "physical_damage", modifiers), 30)
        self.assertEqual(apply_modifiers(10, "physical_damage", reversed(modifiers)), 30)

    def test_base_unchanged_and_removal_updates_immediately(self):
        item = weapon((TEST_POOL[0], TEST_POOL[2]))
        for _ in range(3):
            self.assertEqual((item.final_min_damage, item.final_max_damage), (18, 18))
        self.assertEqual((item.min_damage, item.max_damage, item.crit_chance), (10, 10, 0.1))
        item.remove_affix(TEST_POOL[0])
        self.assertEqual(item.final_min_damage, 12)
        item.set_affixes(())
        self.assertEqual(item.final_min_damage, 10)

    def test_weapon_level_scales_base_before_unchanged_affixes(self):
        item = weapon((TEST_POOL[0], TEST_POOL[2]), level=8)

        self.assertEqual(item.get_scaled_base_damage_range(), (15, 15))
        self.assertEqual(item.final_min_damage, 24)  # floor((10 * 1.56 + 5) * 1.20)
        self.assertEqual(TEST_POOL[0].modifiers[0].value, 5)
        self.assertEqual(TEST_POOL[2].modifiers[0].value, 20)

    def test_weapon_level_must_be_positive_integer(self):
        for invalid_level in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                weapon(level=invalid_level)

    def test_names_do_not_control_behavior_and_tier_does_not_scale_values(self):
        renamed = Affix("other", "Любое название", AffixType.SUFFIX, 99,
                        TEST_POOL[0].modifiers)
        self.assertEqual(weapon((renamed,)).final_min_damage, 15)

    def test_physical_modifier_does_not_affect_other_damage_types(self):
        for kind in (Damage_type.ASTRAL, Damage_type.ELEMENTAL):
            self.assertEqual(weapon((TEST_POOL[0],), damage_type=kind).final_min_damage, 10)

    def test_crit_modifiers_and_clamp(self):
        item = weapon((TEST_POOL[1], TEST_POOL[3]))
        self.assertAlmostEqual(item.final_crit_chance, 0.225)
        self.assertEqual(item.crit_chance, 0.1)
        item.crit_chance = 1
        self.assertEqual(item.final_crit_chance, 1)

    def test_damage_rounding_and_nonnegative_bounds(self):
        fractional = Affix("fraction", "", AffixType.PREFIX, 1,
                           (Modifier("physical_damage", ModifierOperation.FLAT, 0.9),))
        item = weapon((fractional,))
        self.assertEqual(item.final_min_damage, 10)
        item.min_damage = 0
        item.max_damage = 0
        player = Player("Hero", item)
        with patch("random.random", return_value=0.99):
            self.assertEqual(player.attack()[0], 0)

    def test_equipment_replacement_removal_and_two_handed_no_double_bonus(self):
        item = weapon((TEST_POOL[0], TEST_POOL[2]))
        player = Player("Hero", item)
        player.strength = 2
        with patch("random.random", return_value=0.99):
            self.assertEqual(item.get_damage_range(), (18, 18))
            self.assertEqual(player.attack(), (20, False))
            item.remove_affix(TEST_POOL[0])
            self.assertEqual(player.attack(), (14, False))
            replacement = weapon()
            player.inventory.add_item(replacement)
            self.assertTrue(player.equip_weapon(replacement))
            self.assertEqual(player.attack(), (12, False))
            self.assertTrue(player.unequip_weapon())
            self.assertEqual(player.attack(), (12, False))
            self.assertTrue(player.equip_weapon(item))
            self.assertEqual(player.attack(), (14, False))

    def test_player_uses_final_crit_with_existing_cap(self):
        player = Player("Hero", weapon((TEST_POOL[1], TEST_POOL[3])))
        with patch("random.random", return_value=0.2):
            self.assertEqual(player.attack(), (20, True))
        player.dexterity = 100
        with patch("random.random", return_value=0.31):
            self.assertEqual(player.attack(), (10, False))

    def test_menu_uses_final_stats(self):
        item = weapon(TEST_POOL)
        self.assertIn("18–18", format_item_for_menu(item))
        output = io.StringIO()
        with redirect_stdout(output), patch("builtins.input", return_value="0"):
            _show_weapon_details(item, False)
        self.assertIn("18–18", output.getvalue())
        self.assertIn("23%", output.getvalue())

    def test_copy_preserves_rarity_and_independent_affix_collection(self):
        with patch.dict(ITEMS, {"test": weapon(TEST_POOL, rarity=Rarity.EPIC)}):
            first, second = create_item("test"), create_item("test")
            first.remove_affix(TEST_POOL[0])
            self.assertEqual(len(second.affixes), 4)
            self.assertEqual(len(ITEMS["test"].affixes), 4)
            self.assertEqual(second.rarity, Rarity.EPIC)

    def test_invalid_collection_does_not_replace_existing_affixes(self):
        item = weapon(TEST_POOL)
        third = Affix("third", "", AffixType.PREFIX, 1, ())
        for invalid in ((*TEST_POOL, third), (TEST_POOL[0], TEST_POOL[0])):
            with self.assertRaises(ValueError):
                item.set_affixes(invalid)
            self.assertEqual(item.affixes, TEST_POOL)

    def test_manual_addition_respects_rarity_maximum(self):
        for rarity, maximum in ((Rarity.COMMON, 1), (Rarity.RARE, 2)):
            item = weapon(TEST_POOL[:maximum], rarity=rarity)
            with self.assertRaises(ValueError):
                item.add_affix(TEST_POOL[2])
            self.assertEqual(len(item.affixes), maximum)


class TestAffixGeneration(unittest.TestCase):
    def test_all_rarity_counts_and_type_combinations(self):
        for rarity, counts in ((Rarity.COMMON, {0, 1}), (Rarity.RARE, {1, 2}),
                               (Rarity.EPIC, {3, 4})):
            seen = set()
            combinations = set()
            for seed in range(100):
                result = generate_affixes(rarity, TEST_POOL, random.Random(seed))
                seen.add(len(result))
                prefixes = sum(a.type == AffixType.PREFIX for a in result)
                suffixes = len(result) - prefixes
                combinations.add((prefixes, suffixes))
                self.assertLessEqual(prefixes, 2)
                self.assertLessEqual(suffixes, 2)
                self.assertEqual(len({a.id for a in result}), len(result))
                self.assertTrue(all(a in TEST_POOL for a in result))
                if len(result) == 4:
                    self.assertEqual((prefixes, suffixes), (2, 2))
            self.assertEqual(seen, counts)
            if rarity == Rarity.RARE:
                self.assertTrue({(2, 0), (1, 1), (0, 2)} <= combinations)

    def test_unsupported_rarities(self):
        for rarity in (Rarity.LEGENDARY,):
            with self.assertRaises(ValueError):
                generate_affixes(rarity, TEST_POOL)

    def test_insufficient_pool_is_explicit_and_preserves_weapon(self):
        item = weapon(TEST_POOL, rarity=Rarity.EPIC)
        with self.assertRaises(ValueError):
            item.generate_affixes(TEST_POOL[:2])
        self.assertEqual(item.affixes, TEST_POOL)

    def test_zero_count_with_empty_pool(self):
        self.assertEqual(generate_affixes(Rarity.COMMON, (), Mock(randint=Mock(return_value=0))), ())

    def test_generation_assigns_affixes_and_is_reproducible(self):
        item = weapon(rarity=Rarity.EPIC)
        result = item.generate_affixes(TEST_POOL, random.Random(5))
        self.assertEqual(result, generate_affixes(Rarity.EPIC, TEST_POOL, random.Random(5)))
        self.assertEqual(item.affixes, result)

    def test_duplicate_pool_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_affixes(Rarity.RARE, (TEST_POOL[0], TEST_POOL[0]))


if __name__ == "__main__":
    unittest.main()
