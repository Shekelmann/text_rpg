import gc
import random
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from player import Player, ARMOR_SLOTS
from world import World, LOCATION_LEVEL_RANGES
from encounter import create_enemy, handle_encounter, hunt_optional_enemies
from objects import create_item, ITEMS
from spell import Spell
from damage import Damage_type
from battle import (has_usable_action, create_player_turn_state, ATTACK_ACTION_KIND,
                    MAGIC_ACTION_KIND, CONSUMABLE_ACTION_KIND, get_combat_spell_options,
                    finish_victory, battle)


def costly_spell():
    return Spell('test_cost', 'TEST: заклинание', 'Тестовое описание',
                 cost=5, resource='mana', damage=2, damage_type=Damage_type.ASTRAL)


class TestRevisionRules(unittest.TestCase):
    def test_first_and_optional_encounters_respect_player_and_zone(self):
        for seed in range(15):
            player, world, seen = Player('Hero', None), World(random.Random(seed)), []
            with patch('encounter.random.choice', return_value='leshy'), patch('encounter.battle', side_effect=lambda p, e, *args: seen.append(e.level) or True):
                self.assertTrue(handle_encounter(player, 'forest', world))
                with patch('encounter.choose_optional_enemy', return_value=0):
                    hunt_optional_enemies(player, 'forest', world)
            self.assertGreater(len(seen), 1)
            self.assertEqual(set(seen), {1})
        world = World(random.Random(4))
        for location, (low, high) in LOCATION_LEVEL_RANGES.items():
            self.assertEqual(world.prepare_encounter_levels(location, 100), (low, high))
        world = World(random.Random(4))
        self.assertEqual(world.prepare_encounter_levels('mountain', 1), (4, 4))
        self.assertEqual(world.prepare_encounter_levels('forest', 1), (1, 1))
        self.assertEqual(world.prepare_encounter_levels('forest', 8), (1, 1))

    def test_low_mp_does_not_end_turn_with_other_usable_actions(self):
        player, enemy = Player('Hero', None), create_enemy('goblin', 1)
        player.learn_spell(costly_spell())
        player.mana = 0
        state = create_player_turn_state(player)
        self.assertTrue(has_usable_action(player, enemy, state))
        state.use(ATTACK_ACTION_KIND)
        self.assertFalse(has_usable_action(player, enemy, state))
        player.inventory.add_item(create_item('mana'))
        state.available_actions.add(CONSUMABLE_ACTION_KIND)
        self.assertTrue(has_usable_action(player, enemy, state))
        state.use(CONSUMABLE_ACTION_KIND)
        self.assertFalse(has_usable_action(player, enemy, state))
        player.mana = 5
        state.action_points = 1
        self.assertTrue(has_usable_action(player, enemy, state))
        state.use(MAGIC_ACTION_KIND, 1)
        self.assertFalse(has_usable_action(player, enemy, state))

    def test_auto_end_needs_no_extra_input_and_defeat_gives_no_gold(self):
        player, enemy = Player('Hero', None), create_enemy('goblin', 1)
        player.learn_spell(costly_spell())
        player.mana = 0
        gold = player.gold
        def fatal_hit(*args):
            player.health = 0
            return ['TEST']
        with patch('builtins.input', side_effect=['1']) as read, patch('player.input', return_value=''), patch.object(player, 'attack', return_value=(0, False)), patch('battle.enemy_turn', side_effect=fatal_hit) as hit, patch('battle.show_messages'), patch('battle.show_battle_screen'):
            self.assertFalse(battle(player, enemy))
        self.assertEqual(read.call_count, 1)
        hit.assert_called_once()
        self.assertEqual(player.gold, gold)

    def test_victory_gold_floor_and_existing_higher_reward(self):
        for level, difficulty, fixed, expected in ((1, 1, 0, 2), (3, 1, 0, 6), (2, 1.5, 0, 6), (1, 1, 20, 20)):
            player, enemy = Player('Hero', None), create_enemy('goblin', level)
            enemy.difficulty, enemy.gold = difficulty, (fixed, fixed)
            gold = player.gold
            with patch('battle.show_messages'), patch('battle.allocate_stat_points'), patch.object(player, 'add_exp'), patch('battle.generate_loot', return_value=[]), patch('builtins.input', return_value=''):
                self.assertTrue(finish_victory(player, enemy, []))
            self.assertEqual(player.gold-gold, expected)

    def test_direct_tavern_entry_uses_existing_world_paths(self):
        from main import get_location_menu_options, enter_location
        world, player = World(random.Random(2)), Player('Hero', None)
        self.assertIn(('tavern', 'Таверна'), get_location_menu_options(world, 'village'))
        self.assertTrue(enter_location(player, world, 'tavern'))
        self.assertEqual(player.current_location, 'tavern')
        self.assertIn('npc:heinrich', dict(get_location_menu_options(world, 'tavern')))
        self.assertFalse(enter_location(player, world, 'cave'))
        self.assertTrue(enter_location(player, world, 'village'))

    def test_armor_metadata_affixes_and_full_backpack_swap(self):
        from affix import Affix, AffixType, Modifier, ModifierOperation
        from rarity import Rarity
        from objects import ARMOR
        self.assertEqual(ARMOR_SLOTS, ('armor',))
        self.assertEqual(set(ARMOR), {'leather_armor'})
        self.assertFalse(any(key in ITEMS for key in ('leather_helmet', 'leather_chest', 'leather_boots', 'leather_gloves')))
        first, second = create_item('leather_armor'), create_item('leather_armor')
        first.level, first.rarity = 3, Rarity.RARE
        first.set_affixes((Affix('test_armor', 'TEST', AffixType.PREFIX, 1,
                               (Modifier('armor', ModifierOperation.FLAT, 3),)),))
        player = Player('Hero', None)
        player.inventory.add_item(first)
        self.assertTrue(player.equip_armor(first))
        self.assertEqual(player.get_armor_defense(), 5)
        player.inventory.add_item(second)
        for _ in range(19):
            player.inventory.add_item(create_item('dagger'))
        self.assertTrue(player.equip_armor(second))
        self.assertEqual(len(player.inventory.items), 20)
        self.assertEqual(player.get_armor_defense(), 2)
        self.assertFalse(player.unequip_armor())
        self.assertIs(player.armor, second)
        self.assertEqual(create_item('leather_armor').affixes, ())


class TestRevisionGUI(unittest.TestCase):
    def setUp(self):
        gc.collect()
        self.root = tk.Tk()
        from gui import GameWindow
        self.app = GameWindow(self.root)
        self.root.update()

    def tearDown(self):
        self.app.close()
        self.app = self.root = None
        gc.collect()

    def test_heinrich_and_tavern_visible_without_scrolling(self):
        from main import get_location_menu_options
        from gui import Prompt
        from gui_views import character_snapshot
        player, world = Player('Hero', None), World(random.Random(4))
        self.app.update_character(character_snapshot(player))
        for location, label in (('village', 'Таверна'), ('tavern', 'Поговорить: Генрих')):
            options = get_location_menu_options(world, location)
            self.app.routes = {action:str(i) for i,(action, _) in enumerate(options, 1)}
            choices = tuple((str(i), name) for i, (_,name) in enumerate(options, 1))
            self.app.show_prompt(Prompt('Действия', 'location', choices))
            self.root.update()
            button = next(b for b in self.app.buttons.winfo_children() if b.cget('text') == label)
            self.assertLessEqual(button.winfo_y()+button.winfo_height(), self.app.action_canvas.winfo_height())
            self.assertFalse(any(b.cget('text')[0].isdigit() for b in self.app.buttons.winfo_children()))

    def test_disabled_spell_tooltip_and_mouse_keyboard_guard(self):
        import game_io
        from gui import Prompt
        from interface import show_battle_screen
        player, enemy = Player('Hero', None), create_enemy('goblin', 1)
        spell = costly_spell()
        player.learn_spell(spell)
        player.mana = 0
        metadata = get_combat_spell_options(player, enemy)
        with game_io.use_backend(self.app.io):
            show_battle_screen(player, enemy, [], actions=['1 - TEST', '0 - Назад'], spell_options=metadata)
        deadline = time.monotonic()+1
        while self.app.last_screen.get('kind') != 'battle' and time.monotonic()<deadline:
            self.root.update()
            time.sleep(.01)
        self.app.show_prompt(Prompt('Выберите', 'spells', (('1', spell.name), ('0', 'Назад'))))
        self.root.update()
        button = next(b for b in self.app.buttons.winfo_children() if b.cget('text') == spell.name)
        self.assertEqual(str(button.cget('state')), 'disabled')
        button.invoke()
        self.app.submit('1')
        self.assertTrue(self.app.io.answers.empty())
        self.app.action_tooltip.delay_ms = 1
        button.event_generate('<Enter>')
        deadline = time.monotonic()+1
        while self.app.action_tooltip.window is None and time.monotonic()<deadline:
            self.root.update()
            time.sleep(.01)
        self.assertIsNotNone(self.app.action_tooltip.window)
        self.assertIn('5 MP', '\n'.join(metadata['1']['tooltip']))
        self.assertIn(spell.description, '\n'.join(metadata['1']['tooltip']))
        self.assertEqual(player.mana, 0)
        player.mana = 5
        self.assertTrue(get_combat_spell_options(player, enemy)['1']['enabled'])
