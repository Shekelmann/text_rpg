import gc
import pickle
import random
import tkinter as tk
import unittest
from unittest.mock import patch

from action_layout import location_action_layout, CATEGORIES
from battle import player_turn, create_player_turn_state, ATTACK_ACTION_KIND
from character_class import CLASSES
from encounter import create_enemy
from objects import create_item
from player import Player
from effects import Poison, Bleeding
from affix import Affix, AffixType, OnHitEffect, OnHitEffectType, Modifier, ModifierOperation


def paired_player():
    player = Player('Hero', create_item('dagger'), CLASSES['daredevil'])
    second = create_item('dagger')
    player.inventory.add_item(second)
    assert player.equip_weapon(second)
    return player


class TestDualDaggers(unittest.TestCase):
    def test_only_daredevil_daggers_can_pair(self):
        for class_id in CLASSES:
            for weapon_id in ('sword', 'dagger', 'staff', '2 handed axe'):
                player = Player('Hero', create_item('dagger'), CLASSES[class_id])
                item = create_item(weapon_id)
                player.inventory.add_item(item)
                expected = class_id == 'daredevil' and weapon_id == 'dagger'
                self.assertEqual(player.equip_weapon(item, 'off_hand'), expected)
                self.assertEqual(item in player.inventory.items, not expected)

    def test_each_hand_replaces_and_removes_without_duplicates(self):
        player = paired_player()
        old_main, old_off = player.attack_weapons()
        replacement = create_item('dagger')
        player.inventory.add_item(replacement)
        self.assertTrue(player.equip_weapon(replacement, 'off_hand'))
        self.assertIs(player.main_hand, old_main)
        self.assertIs(player.off_hand, replacement)
        self.assertIn(old_off, player.inventory.items)
        self.assertTrue(player.unequip_weapon('off_hand'))
        self.assertTrue(player.equip_weapon(old_off, 'off_hand'))
        self.assertTrue(player.unequip_weapon('main_hand'))
        self.assertIs(player.main_hand, old_off)
        self.assertIsNone(player.off_hand)
        items = player.inventory.items + [player.main_hand]
        self.assertEqual(len(items), len({id(item) for item in items}))

    def test_full_backpack_two_handed_switch_is_atomic(self):
        player = paired_player()
        hands = player.attack_weapons()
        item = create_item('2 handed axe')
        player.inventory.add_item(item)
        for _ in range(19):
            player.inventory.add_item(create_item('sword'))
        before = player.inventory.slots
        self.assertFalse(player.equip_weapon(item))
        self.assertEqual(player.inventory.slots, before)
        self.assertEqual(player.attack_weapons(), hands)
        self.assertFalse(player.unequip_weapon('off_hand'))
        player.inventory.remove_item(player.inventory.items[-1])
        self.assertTrue(player.equip_weapon(item))
        self.assertIs(player.main_hand, item)
        self.assertIs(player.off_hand, item)
        self.assertTrue(all(weapon in player.inventory.items for weapon in hands))

    def test_main_replacement_preserves_pair_or_returns_incompatible_offhand(self):
        player = paired_player()
        main, off = player.attack_weapons()
        dagger = create_item('dagger')
        player.inventory.add_item(dagger)
        self.assertTrue(player.equip_weapon(dagger, 'main_hand'))
        self.assertEqual(player.attack_weapons(), (dagger, off))
        self.assertIn(main, player.inventory.items)
        sword = create_item('sword')
        player.inventory.add_item(sword)
        self.assertTrue(player.equip_weapon(sword))
        self.assertEqual(player.attack_weapons(), (sword,))
        self.assertIsNone(player.off_hand)
        self.assertIn(off, player.inventory.items)
        self.assertIn(dagger, player.inventory.items)

    def test_each_hit_uses_own_damage_crit_and_effects(self):
        player = paired_player()
        first, second = player.attack_weapons()
        first.min_damage = first.max_damage = 3
        second.min_damage = second.max_damage = 7
        first.crit_chance, second.crit_chance = 0, .3
        first.set_affixes((Affix('test_poison', 'TEST', AffixType.PREFIX, 1, (),
                                effects=(OnHitEffect(OnHitEffectType.POISON, 3),)),))
        second.set_affixes((Affix('test_bleed', 'TEST', AffixType.PREFIX, 1,
                                 (Modifier('attack_physical_damage', ModifierOperation.FLAT, 4),),
                                 effects=(OnHitEffect(OnHitEffectType.BLEEDING, 2, 3),)),))
        enemy = create_enemy('goblin', 1)
        enemy.dodge_chance = 0
        enemy.health = enemy.max_health = 500
        state = create_player_turn_state(player)
        rolled = ((3 + player.strength), 2 * (7 + player.strength + 4))
        expected = sum(max(0, damage - enemy.armor) for damage in rolled)
        with patch('builtins.input', return_value='1'), patch('player.random.random', side_effect=[.9, .1]), patch.object(player, 'trigger_action_effects', wraps=player.trigger_action_effects) as trigger:
            messages = player_turn(player, enemy, turn_state=state)
        self.assertEqual(enemy.health, 500 - expected)
        self.assertEqual(sum('Критический' in line for line in messages), 1)
        self.assertTrue(enemy.effects.contains(Poison))
        self.assertTrue(enemy.effects.contains(Bleeding))
        self.assertFalse(state.can_use(ATTACK_ACTION_KIND))
        trigger.assert_called_once()

    def test_first_kill_skips_second_weapon(self):
        player = paired_player()
        enemy = create_enemy('goblin', 1)
        enemy.dodge_chance = 0
        enemy.health = 1
        with patch('builtins.input', return_value='1'), patch.object(player.off_hand, 'on_hit') as on_hit, patch.object(player, 'attack', wraps=player.attack) as attack:
            player_turn(player, enemy)
        self.assertFalse(enemy.is_alive())
        self.assertEqual(attack.call_count, 1)
        on_hit.assert_not_called()

    def test_single_weapon_classes_still_hit_once(self):
        for class_id, item_id in (('bruiser', 'sword'), ('herald', 'staff'), ('daredevil', 'dagger')):
            player = Player('Hero', create_item(item_id), CLASSES[class_id])
            enemy = create_enemy('goblin', 1)
            enemy.dodge_chance = 0
            enemy.health = 500
            with patch('builtins.input', return_value='1'), patch.object(player, 'attack', wraps=player.attack) as attack:
                player_turn(player, enemy)
            self.assertEqual(attack.call_count, 1)

    def test_player_roundtrip_preserves_both_distinct_weapons_and_affixes(self):
        player = paired_player()
        player.off_hand.set_affixes((Affix('test_dodge', 'TEST', AffixType.PREFIX, 1,
                                         (Modifier('dodge_chance', ModifierOperation.FLAT, .1),)),))
        restored = pickle.loads(pickle.dumps(player))
        self.assertIsNot(restored.main_hand, restored.off_hand)
        self.assertEqual(len(restored.attack_weapons()), 2)
        self.assertEqual(restored.off_hand.affixes, player.off_hand.affixes)
        self.assertAlmostEqual(restored.get_dodge_chance(), .13)
        self.assertTrue(restored.unequip_weapon('off_hand'))
        self.assertEqual(len(player.attack_weapons()), 2)


class TestCategorizedActions(unittest.TestCase):
    def test_order_is_deterministic_for_context_changes(self):
        from main import get_location_menu_options
        from world import World
        world = World(random.Random(5))
        observed = []
        for state in ('ordinary', 'enemies', 'partial', 'cleared', 'loot'):
            location = 'village' if state == 'ordinary' else 'forest'
            if state == 'enemies':
                world.complete_main_encounter('forest')
            if state == 'partial':
                world.defeat_optional_enemy('forest', 0)
            if state == 'cleared':
                while world.can_hunt_optional_enemies('forest'):
                    world.defeat_optional_enemy('forest', 0)
            if state == 'loot':
                world.add_ground_loot('forest', create_item('sword'))
            actions = get_location_menu_options(world, location)
            choices = tuple((str(i), name) for i, (_, name) in enumerate(actions, 1))
            routes = {action: str(i) for i, (action, _) in enumerate(actions, 1)}
            layout = location_action_layout(choices, routes)
            self.assertEqual(layout, location_action_layout(tuple(reversed(choices)), routes))
            rows = {action: row for key, label, row, column, count in layout
                    for action, value in routes.items() if value == key}
            observed.append(rows)
            if 'hunt' in rows:
                self.assertEqual(rows['hunt'], CATEGORIES.index('hostile'))
            self.assertEqual(rows['move'], CATEGORIES.index('travel'))
        self.assertEqual(observed[1]['hunt'], observed[2]['hunt'])
        self.assertNotIn('hunt', observed[3])
        self.assertEqual(observed[3]['chest'], observed[4]['chest'])


class TestDualInventoryGUI(unittest.TestCase):
    def test_each_hand_is_visible_and_managed_in_inventory(self):
        from inventory_gui import InventoryWindow
        gc.collect()
        root = tk.Tk()
        player = paired_player()
        window = InventoryWindow(root, player)
        try:
            root.update()
            self.assertIn(player.off_hand.name, window.hand_labels['off_hand'].cget('text'))
            window.unequip_buttons['off_hand'].invoke()
            self.assertIsNone(player.off_hand)
            window.weapon_target.set('off_hand')
            self.assertTrue(window.equip_slot(0))
            self.assertEqual(len(player.attack_weapons()), 2)
            window.unequip_buttons['main_hand'].invoke()
            self.assertIsNotNone(player.main_hand)
            self.assertIsNone(player.off_hand)
        finally:
            window.close()
            root.destroy()
            gc.collect()
