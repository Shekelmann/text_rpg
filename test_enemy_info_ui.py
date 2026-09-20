import pickle
import unittest
from unittest.mock import patch

import game_io
from battle import (
    ABILITY_ACTION_KIND,
    PlayerTurnState,
    show_messages,
    use_ability_action,
)
from character_class import CLASSES
from damage import Damage_type
from encounter import create_enemy
from enemy import Enemy
from gui import DesktopIO
from gui_views import enemy_combat_snapshot
from interface import show_battle_screen
from item import Item
from player import Player


class TestEnemyInformationUI(unittest.TestCase):
    def test_armor_is_always_present_in_snapshot(self):
        unarmored = enemy_combat_snapshot(create_enemy("wolf", 1))
        armored = enemy_combat_snapshot(create_enemy("goblin", 1))

        self.assertEqual(unarmored["enemy_armor"], 0)
        self.assertEqual(unarmored["enemy_armor_tooltip"][0], "Броня: 0")
        self.assertEqual(armored["enemy_armor"], 3)
        self.assertEqual(armored["enemy_armor_tooltip"][0], "Броня: 3")

    def test_physical_astral_and_dual_capabilities_are_separate_from_intent(self):
        physical = enemy_combat_snapshot(create_enemy("goblin", 1))
        astral = enemy_combat_snapshot(create_enemy("likho", 1))
        dual_enemy = Enemy(
            "Dual", 100, 1, 2, 0, Damage_type.PHYSICAL,
            damage_types=(Damage_type.PHYSICAL, Damage_type.ASTRAL),
        )
        dual = enemy_combat_snapshot(dual_enemy)

        self.assertEqual(
            tuple(entry["id"] for entry in physical["enemy_damage_types"]),
            ("physical",),
        )
        self.assertEqual(
            tuple(entry["id"] for entry in astral["enemy_damage_types"]),
            ("astral",),
        )
        self.assertEqual(
            tuple(entry["id"] for entry in dual["enemy_damage_types"]),
            ("physical", "astral"),
        )
        self.assertEqual(dual["enemy_intent"]["id"], "physical_attack")

    def test_possible_dots_are_compact_and_explained_by_tooltip(self):
        enemy = Enemy(
            "Venomous", 100, 1, 2, 0, Damage_type.PHYSICAL,
            damage_type_effects={
                Damage_type.PHYSICAL: ("poison", "bleeding"),
            },
        )

        physical = enemy_combat_snapshot(enemy)["enemy_damage_types"][0]

        self.assertEqual(physical["dot_effects"], ("Яд", "Кровотечение"))
        self.assertTrue(physical["icon"].endswith("•"))
        self.assertIn("Яд, Кровотечение", physical["tooltip"][-1])


class TestDrainPresentationContract(unittest.TestCase):
    def test_battle_screen_accepts_resource_events(self):
        player = Player("Hero", None)
        enemy = create_enemy("goblin", 1)
        backend = DesktopIO()

        with game_io.use_backend(backend):
            show_battle_screen(
                player,
                enemy,
                messages=("Восстановлено 3 MP.",),
                resource_events=({
                    "target": "player",
                    "resource": "mana",
                    "before": 0,
                    "after": 3,
                    "amount": 3,
                    "kind": "resource_restore",
                },),
            )

        screens = []
        while not backend.events.empty():
            event, payload = backend.events.get_nowait()
            if event == "screen":
                screens.append(payload)
        self.assertEqual(screens[-1]["resource_events"][0]["amount"], 3)

    def test_drain_returns_to_battle_with_all_three_visual_events(self):
        player = Player("Herald", None, CLASSES["herald"])
        player.equip_ability("drain", 0)
        player.health -= 10
        player.mana = 0
        enemy = create_enemy("goblin", 1)
        result = use_ability_action(
            player,
            enemy,
            "drain",
            PlayerTurnState({ABILITY_ACTION_KIND}, action_points=2),
        )
        backend = DesktopIO()

        with game_io.use_backend(backend), patch("battle.time.sleep"):
            show_messages(player, enemy, [], result.messages)

        screens = []
        while not backend.events.empty():
            event, payload = backend.events.get_nowait()
            if event == "screen":
                screens.append(payload)
        self.assertTrue(result.success)
        self.assertTrue(any(screen["health_events"] for screen in screens))
        self.assertTrue(any(screen["resource_events"] for screen in screens))
        mana_event = next(
            screen["resource_events"][0]
            for screen in screens if screen["resource_events"]
        )
        self.assertEqual((mana_event["resource"], mana_event["amount"]),
                         ("mana", 3))


class TestModerateManaScaling(unittest.TestCase):
    def test_starting_class_mana_is_moderate_and_uses_one_per_int(self):
        expected = {"bruiser": 10, "daredevil": 10, "herald": 13}
        for class_id, maximum in expected.items():
            with self.subTest(class_id=class_id):
                player = Player("Hero", None, CLASSES[class_id])
                self.assertEqual(player.max_mana, maximum)

    def test_equipment_int_bonus_recalculates_and_removal_caps_mana(self):
        player = Player("Hero", None)
        amulet = Item("Mind amulet", "accessory", False)
        amulet.slot = "amulet"
        amulet.intelligence_bonus = 3
        player.inventory.add_item(amulet)

        self.assertTrue(player.equip_accessory(amulet))
        self.assertEqual(player.max_mana, 11)
        self.assertEqual(player.mana, 11)
        self.assertTrue(player.unequip_accessory("amulet"))
        self.assertEqual(player.max_mana, 8)
        self.assertEqual(player.mana, 8)

    def test_old_save_adopts_current_class_mana_base(self):
        player = Player("Herald", None, CLASSES["herald"])
        player.base_max_mana = 20
        player.max_mana = 23
        player.mana = 23

        restored = pickle.loads(pickle.dumps(player))

        self.assertEqual(restored.base_max_mana, 10)
        self.assertEqual(restored.max_mana, 13)
        self.assertEqual(restored.mana, 13)


if __name__ == "__main__":
    unittest.main()
