import random
import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from encounter import create_enemy, handle_encounter, hunt_optional_enemies
from interface import choose_optional_enemy
from main import get_location_menu_options, move_player
from objects import ENEMIES
from player import Player
from world import (
    LOCATION_ENEMIES,
    LOCATION_LEVELS,
    LOCATION_RARITY_CHANCES,
    RARITY_CHANCES,
    World,
)


def menu_labels(world, location_id):
    return [label for _, label in get_location_menu_options(world, location_id)]


class CountingRandom:
    def __init__(self):
        self.randint_calls = 0
        self.choice_calls = 0

    def randint(self, minimum, maximum):
        self.randint_calls += 1
        return minimum

    def choice(self, values):
        self.choice_calls += 1
        return values[0]


class TestOptionalEnemyState(unittest.TestCase):
    def test_location_enemy_pools_are_ordered_as_configured(self):
        self.assertEqual(
            LOCATION_ENEMIES,
            {
                "forest": ["wolf", "goblin", "likho", "leshy"],
                "cave": ["spider", "mutant", "skeleton", "draugr"],
                "witch's hut": ["goblin", "spirit", "undead"],
                "goblins_camp": ["goblin"],
                "mountain": ["wolf", "orc", "mountain_troll"],
                "old man's hut": ["goblin", "bandit", "orc"],
                "plains": ["orc"],
            },
        )

    def test_combat_location_levels_are_configured(self):
        self.assertEqual(
            LOCATION_LEVELS,
            {
                "forest": 1,
                "cave": 2,
                "witch's hut": 2,
                "goblins_camp": 3,
                "mountain": 4,
                "old man's hut": 5,
                "plains": 15,
            },
        )

    def test_location_pools_are_ordered_by_base_health(self):
        for location_id, enemy_ids in LOCATION_ENEMIES.items():
            health_values = [ENEMIES[enemy_id]["health"] for enemy_id in enemy_ids]
            with self.subTest(location=location_id):
                self.assertEqual(health_values, sorted(health_values))

    def test_optional_enemies_are_unavailable_before_main_encounter(self):
        world = World(random.Random(1))

        self.assertFalse(world.can_hunt_optional_enemies("forest"))
        self.assertNotIn(
            "Добить оставшихся врагов",
            menu_labels(world, "forest"),
        )

    def test_each_combat_location_gets_five_to_nine_enemies(self):
        world = World(random.Random(2))

        for location_id in LOCATION_ENEMIES:
            enemy_count = len(world.get_optional_enemies(location_id))
            self.assertGreaterEqual(enemy_count, 5)
            self.assertLessEqual(enemy_count, 9)

    def test_safe_locations_do_not_get_optional_enemies(self):
        world = World(random.Random(3))

        for location_id in ("village", "tavern", "mine"):
            self.assertIsNone(world.get_combat_state(location_id))
            self.assertEqual(world.get_optional_enemies(location_id), ())

    def test_optional_enemies_are_generated_from_location_pool(self):
        class PoolCheckingRandom(CountingRandom):
            def __init__(self):
                super().__init__()
                self.pools = []

            def choice(self, values):
                self.pools.append(values)
                return super().choice(values)

        rng = PoolCheckingRandom()
        World(rng)

        for location_id, pool in LOCATION_ENEMIES.items():
            self.assertIn(pool, rng.pools, location_id)

    def test_goblin_camp_has_higher_elite_chance(self):
        self.assertGreater(
            LOCATION_RARITY_CHANCES["goblins_camp"]["elite"],
            RARITY_CHANCES["elite"],
        )

    def test_create_enemy_uses_given_location_level(self):
        for location_id, level in LOCATION_LEVELS.items():
            with self.subTest(location=location_id):
                enemy = create_enemy(LOCATION_ENEMIES[location_id][0], level)
                self.assertEqual(enemy.level, level)

    @patch("builtins.input", return_value="2")
    def test_mine_is_blocked_with_message(self, _mock_input):
        player = Player("Hero", None)
        player.current_location = "mountain"
        world = World(random.Random(10))
        output = io.StringIO()

        with redirect_stdout(output):
            move_player(player, world)

        self.assertEqual(player.current_location, "mountain")
        self.assertEqual(world.move("mountain", 1), "mountain")
        self.assertIn("Шахта завалена.", output.getvalue())

    def test_list_is_generated_only_during_world_creation(self):
        rng = CountingRandom()
        world = World(rng)
        initial_calls = (rng.randint_calls, rng.choice_calls)

        world.get_optional_enemies("forest")
        world.get_optional_enemies("forest")
        world.get_optional_enemies("cave")

        self.assertEqual(rng.randint_calls, len(LOCATION_ENEMIES))
        self.assertEqual((rng.randint_calls, rng.choice_calls), initial_calls)

    def test_defeated_enemy_disappears_and_others_remain(self):
        world = World(random.Random(4))
        world.complete_main_encounter("forest")
        enemies_before = world.get_optional_enemies("forest")

        self.assertTrue(world.defeat_optional_enemy("forest", 0))

        self.assertEqual(
            world.get_optional_enemies("forest"),
            enemies_before[1:],
        )

    def test_defeated_enemy_does_not_return_after_leaving_location(self):
        world = World(random.Random(5))
        world.complete_main_encounter("forest")
        world.defeat_optional_enemy("forest", 0)
        remaining = world.get_optional_enemies("forest")

        self.assertEqual(world.move("forest", 0), "village")
        self.assertEqual(world.move("village", 0), "forest")
        self.assertEqual(world.get_optional_enemies("forest"), remaining)

    def test_full_clear_replaces_hunt_with_chest(self):
        world = World(random.Random(6))
        world.complete_main_encounter("forest")
        while world.get_optional_enemies("forest"):
            world.defeat_optional_enemy("forest", 0)

        labels = menu_labels(world, "forest")
        self.assertTrue(world.is_location_cleared("forest"))
        self.assertNotIn("Добить оставшихся врагов", labels)
        self.assertIn("Открыть сундук", labels)

    def test_opened_chest_is_not_available_again(self):
        world = World(random.Random(7))
        world.complete_main_encounter("forest")
        while world.get_optional_enemies("forest"):
            world.defeat_optional_enemy("forest", 0)

        self.assertTrue(world.open_chest("forest"))
        self.assertFalse(world.is_chest_available("forest"))
        self.assertFalse(world.open_chest("forest"))
        self.assertNotIn("Открыть сундук", menu_labels(world, "forest"))

    @patch("interface.clear")
    @patch("builtins.input", return_value="2")
    def test_enemy_menu_uses_current_list_and_returns_selected_index(
        self,
        _mock_input,
        _mock_clear,
    ):
        output = io.StringIO()
        with redirect_stdout(output):
            selected = choose_optional_enemy(["Волк", "Гоблин"])

        self.assertEqual(selected, 1)
        self.assertIn("1. Волк", output.getvalue())
        self.assertIn("2. Гоблин", output.getvalue())
        self.assertIn("0. Назад", output.getvalue())


class TestOptionalEnemyEncounters(unittest.TestCase):
    def setUp(self):
        self.player = Player("Hero", None)
        self.world = World(random.Random(8))

    @patch("encounter.battle", return_value=True)
    @patch("encounter.random.choice", return_value="goblin")
    @patch("encounter.random.choices", return_value=["elite"])
    def test_forest_supports_elite_encounter_without_key_error(
        self,
        _mock_choices,
        _mock_choice,
        _mock_battle,
    ):
        self.assertTrue(handle_encounter(self.player, "forest", self.world))
        self.assertTrue(
            self.world.get_combat_state("forest")["main_encounter_completed"]
        )

    @patch("encounter.battle", return_value=True)
    @patch("encounter.create_enemy", return_value=Mock())
    @patch("encounter.random.choice", return_value="goblin")
    @patch("encounter.random.choices", return_value=["common"])
    def test_main_victory_unlocks_optional_enemies(
        self,
        _mock_choices,
        _mock_choice,
        _mock_create_enemy,
        _mock_battle,
    ):
        self.assertTrue(handle_encounter(self.player, "forest", self.world))

        _mock_choice.assert_called_once_with(LOCATION_ENEMIES["forest"])
        _mock_create_enemy.assert_called_once_with("goblin", 1, "common")

        self.assertTrue(self.world.can_hunt_optional_enemies("forest"))
        self.assertIn(
            "Добить оставшихся врагов",
            menu_labels(self.world, "forest"),
        )

    @patch("encounter.battle")
    def test_completed_main_encounter_is_not_started_again(self, mock_battle):
        self.world.complete_main_encounter("forest")

        self.assertFalse(handle_encounter(self.player, "forest", self.world))
        mock_battle.assert_not_called()

    @patch("encounter.battle", return_value=True)
    @patch("encounter.create_enemy", return_value=Mock())
    @patch("encounter.choose_optional_enemy", side_effect=[0, None])
    def test_winning_optional_battle_removes_only_selected_enemy(
        self,
        _mock_choose,
        _mock_create_enemy,
        _mock_battle,
    ):
        self.world.complete_main_encounter("forest")
        enemies_before = self.world.get_optional_enemies("forest")

        hunt_optional_enemies(self.player, "forest", self.world)

        self.assertEqual(
            self.world.get_optional_enemies("forest"),
            enemies_before[1:],
        )

    @patch("encounter.battle", return_value=False)
    @patch("encounter.create_enemy", return_value=Mock())
    @patch("encounter.choose_optional_enemy", return_value=0)
    def test_losing_optional_battle_keeps_enemy(
        self,
        _mock_choose,
        _mock_create_enemy,
        _mock_battle,
    ):
        self.world.complete_main_encounter("forest")
        enemies_before = self.world.get_optional_enemies("forest")

        hunt_optional_enemies(self.player, "forest", self.world)

        self.assertEqual(
            self.world.get_optional_enemies("forest"),
            enemies_before,
        )


if __name__ == "__main__":
    unittest.main()
