import io
import random
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from encounter import claim_location_chest
from main import open_location_chest
from objects import WEAPONS, generate_chest_reward, get_chest_rarity_chances
from player import Player
from rarity import Rarity
from world import LOCATION_LEVEL_RANGES, World


def clear_location(world, location_id):
    world.complete_main_encounter(location_id)
    while world.get_optional_enemies(location_id):
        world.defeat_optional_enemy(location_id, 0)


class TestChestReward(unittest.TestCase):
    def test_chest_weapon_is_rare_or_epic_with_rare_as_main_chance(self):
        rarities = {
            generate_chest_reward((1, 2), random.Random(seed))["weapon"].rarity
            for seed in range(100)
        }

        self.assertEqual(rarities, {Rarity.RARE, Rarity.EPIC})
        chances = get_chest_rarity_chances((1, 2))
        self.assertGreater(chances[Rarity.RARE], chances[Rarity.EPIC])

    def test_chest_rarity_improves_with_location_level_range(self):
        early = get_chest_rarity_chances((1, 2))
        middle = get_chest_rarity_chances((4, 6))
        late = get_chest_rarity_chances((8, 10))

        self.assertEqual(early, {Rarity.RARE: 0.80, Rarity.EPIC: 0.20})
        self.assertEqual(middle, {Rarity.RARE: 0.65, Rarity.EPIC: 0.35})
        self.assertEqual(late, {Rarity.RARE: 0.50, Rarity.EPIC: 0.50})

    def test_chest_uses_existing_weapon_templates_without_mutating_them(self):
        reward = generate_chest_reward((4, 6), random.Random(4))
        weapon = reward["weapon"]

        self.assertIn(weapon.name, {template.name for template in WEAPONS.values()})
        self.assertTrue(all(template.affixes == () for template in WEAPONS.values()))
        self.assertTrue(all(template.level == 1 for template in WEAPONS.values()))
        self.assertGreaterEqual(weapon.level, 4)
        self.assertLessEqual(weapon.level, 6)

    def test_chest_gold_scales_with_location_level_range(self):
        for location_id, level_range in LOCATION_LEVEL_RANGES.items():
            reward = generate_chest_reward(level_range, random.Random(5))
            with self.subTest(location=location_id):
                self.assertGreaterEqual(reward["gold"], level_range[0] * 5)
                self.assertLessEqual(reward["gold"], level_range[1] * 10)

    def test_cleared_location_chest_can_be_claimed_only_once(self):
        player = Player("Hero", None)
        world = World(random.Random(6))
        clear_location(world, "forest")
        starting_gold = player.gold

        reward = claim_location_chest(player, "forest", world, random.Random(7))
        second_reward = claim_location_chest(player, "forest", world, random.Random(8))

        self.assertIsNotNone(reward)
        self.assertIsNone(second_reward)
        self.assertIn(reward["weapon"], player.inventory.items)
        self.assertEqual(player.gold, starting_gold + reward["gold"])
        self.assertFalse(world.is_chest_available("forest"))

    def test_full_inventory_leaves_chest_weapon_in_location(self):
        player = Player("Hero", None)
        player.inventory.size = 0
        world = World(random.Random(9))
        clear_location(world, "forest")

        reward = claim_location_chest(player, "forest", world, random.Random(10))

        self.assertIsNotNone(reward)
        self.assertTrue(reward["stored_in_location"])
        self.assertEqual(world.get_ground_loot("forest"), (reward["weapon"],))
        self.assertFalse(world.is_chest_available("forest"))

    @patch("builtins.input", return_value="")
    def test_open_chest_shows_weapon_rarity_and_gold(self, _mock_input):
        player = Player("Hero", None)
        player.current_location = "forest"
        world = World(random.Random(12))
        clear_location(world, "forest")
        output = io.StringIO()

        with redirect_stdout(output):
            open_location_chest(player, world)

        text = output.getvalue()
        weapon = player.inventory.items[0]
        self.assertIn(weapon.display_name, text)
        self.assertIn(weapon.rarity.title, text)
        self.assertIn("Золото:", text)


if __name__ == "__main__":
    unittest.main()
