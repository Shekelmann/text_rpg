import pickle
import random
import unittest
from unittest.mock import patch

from main import confirm_rest_at_tavern, get_location_menu_options, rest_at_tavern
from player import Player
from world import World


class TestDaysAndTavernRest(unittest.TestCase):
    def setUp(self):
        self.world = World(random.Random(7))
        self.player = Player("Hero", None)
        self.player.current_location = "tavern"

    def test_new_world_starts_on_day_one_and_tavern_has_rest_action(self):
        self.assertEqual(self.world.day, 1)
        self.assertIn(
            ("rest", "Отдохнуть"),
            get_location_menu_options(self.world, "tavern"),
        )
        self.assertNotIn(
            ("rest", "Отдохнуть"),
            get_location_menu_options(self.world, "village"),
        )

    def test_rest_starts_new_day_restores_resources_and_keeps_player_in_tavern(self):
        self.player.health = 1
        self.player.mana = 0
        self.world.complete_main_encounter("forest")
        original_optional = tuple(
            self.world.get_combat_state("forest")["optional_enemies"]
        )
        self.world.defeat_optional_enemy("forest", 0)

        self.assertTrue(rest_at_tavern(self.player, self.world))

        state = self.world.get_combat_state("forest")
        self.assertEqual(self.world.day, 2)
        self.assertEqual(self.player.health, self.player.max_health)
        self.assertEqual(self.player.mana, self.player.max_mana)
        self.assertEqual(self.player.current_location, "tavern")
        self.assertFalse(state["main_encounter_completed"])
        self.assertEqual(tuple(state["optional_enemies"]), original_optional)

    def test_rest_does_not_reset_chests_or_story_encounters(self):
        normal = self.world.get_combat_state("forest")
        normal["chest_opened"] = True
        story = self.world.get_combat_state("cave")
        story["is_story_encounter"] = True
        story["main_encounter_completed"] = True
        story_enemies = tuple(story["optional_enemies"])

        rest_at_tavern(self.player, self.world)

        self.assertTrue(normal["chest_opened"])
        self.assertTrue(story["main_encounter_completed"])
        self.assertEqual(tuple(story["optional_enemies"]), story_enemies)

    def test_declining_confirmation_changes_nothing(self):
        self.player.health = 3
        with patch("main.input", return_value="0"):
            self.assertFalse(confirm_rest_at_tavern(self.player, self.world))
        self.assertEqual(self.world.day, 1)
        self.assertEqual(self.player.health, 3)

    def test_accepting_confirmation_rests(self):
        self.player.health = 3
        with patch("main.input", return_value="1"):
            self.assertTrue(confirm_rest_at_tavern(self.player, self.world))
        self.assertEqual(self.world.day, 2)
        self.assertEqual(self.player.health, self.player.max_health)

    def test_rest_is_rejected_outside_tavern(self):
        self.player.current_location = "village"
        self.assertFalse(rest_at_tavern(self.player, self.world))
        self.assertEqual(self.world.day, 1)


class TestDayPersistence(unittest.TestCase):
    def test_day_and_current_encounter_state_survive_round_trip(self):
        world = World(random.Random(4))
        world.day = 5
        world.complete_main_encounter("forest")
        restored = pickle.loads(pickle.dumps(world))
        self.assertEqual(restored.day, 5)
        self.assertTrue(
            restored.get_combat_state("forest")["main_encounter_completed"]
        )

    def test_story_completion_survives_round_trip(self):
        world = World(random.Random(4))
        state = world.get_combat_state("forest")
        state["is_story_encounter"] = True
        state["main_encounter_completed"] = True
        restored = pickle.loads(pickle.dumps(world))
        restored.start_new_day(Player("Hero", None), random.Random(5))
        self.assertTrue(
            restored.get_combat_state("forest")["main_encounter_completed"]
        )

    def test_old_world_without_day_loads_as_day_one_without_respawn(self):
        world = World(random.Random(4))
        world.complete_main_encounter("forest")
        del world.day
        del world.get_combat_state("forest")["is_story_encounter"]
        restored = pickle.loads(pickle.dumps(world))
        self.assertEqual(restored.day, 1)
        self.assertTrue(
            restored.get_combat_state("forest")["main_encounter_completed"]
        )
        self.assertFalse(
            restored.get_combat_state("forest")["is_story_encounter"]
        )


if __name__ == "__main__":
    unittest.main()
