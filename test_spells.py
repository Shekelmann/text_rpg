"""Technical spell fixtures live only in tests, never in the content registry."""
import gc
import pickle
import tkinter as tk
import unittest
from unittest.mock import patch

from damage import Damage_type
from effects import Poison, Drain, Regeneration, NON_ATTACK_ACTION
from player import Player
from spell import Spell, CastResult
from spells import SPELLS, STARTING_SPELL_IDS
from character_class import CLASSES


def test_spell(**changes):
    data = dict(id="test_spell", name="TEST: удар", description="Технический пример, не игровой контент",
                cost=3, resource="mana", damage=10, damage_type=Damage_type.ASTRAL)
    data.update(changes)
    return Spell(**data)


class TestSpells(unittest.TestCase):
    def setUp(self):
        self.player = Player("Caster", None)
        self.target = Player("Target", None)
        self.spell = test_spell()

    def test_ownership_modes_remain_separate(self):
        self.assertTrue(self.player.learn_spell(self.spell))
        self.assertFalse(self.player.learn_spell(self.spell))
        self.player.add_scroll(self.spell, 2)
        self.assertTrue(self.player.cast_spell(self.spell.id, self.target).success)
        self.assertEqual(self.player.mana, 7)
        self.assertEqual(self.player.spellbook.learned, (self.spell,))
        self.assertEqual(self.player.spellbook.scrolls, ((self.spell, 2),))
        self.assertTrue(self.player.cast_spell(self.spell.id, self.target, one_shot=True).success)
        self.assertTrue(self.player.cast_spell(self.spell.id, self.target, one_shot=True).success)
        self.assertEqual(self.player.spellbook.scrolls, ())
        self.assertEqual(self.player.spellbook.learned, (self.spell,))
        self.assertEqual(self.player.inventory.items, [])

    def test_rejections_do_not_spend_resources_or_scroll(self):
        self.player.add_scroll(self.spell)
        for target, mana, health in ((None, 10, 120), (self.target, 0, 120), (self.target, 10, 0)):
            self.player.mana, self.player.health = mana, health
            before = self.target.health
            self.assertFalse(self.player.can_cast_spell(self.spell.id, target, one_shot=True))
            self.assertFalse(self.player.cast_spell(self.spell.id, target, one_shot=True).success)
            self.assertEqual(self.player.mana, mana)
            self.assertEqual(self.target.health, before)
            self.assertEqual(self.player.spellbook.scrolls, ((self.spell, 1),))
        self.assertFalse(self.player.cast_spell("unknown", self.target).success)
        self.assertFalse(self.player.cast_spell(self.spell.id, self.target).success)

    def test_direct_astral_damage_uses_int_and_existing_resistance(self):
        self.player.intelligence = 100
        self.target.resistances[Damage_type.ASTRAL] = .5
        self.player.learn_spell(self.spell)
        before = self.target.health
        result = self.player.cast_spell(self.spell.id, self.target)
        self.assertEqual(result.damage, 55)
        self.assertEqual(self.target.health, before - 55)

    def test_effect_instances_are_independent_and_source_is_real_caster(self):
        prototype = Poison(4)
        spell = test_spell(damage=0, effects=(prototype, Drain(4)))
        self.player.learn_spell(spell)
        self.player.cast_spell(spell.id, self.target)
        active = self.target.effects.get_by_stack_key("poison")
        self.assertIsNot(active, prototype)
        self.assertIs(self.target.effects.get_by_stack_key("drain").source, self.player)
        self.target.trigger_turn_start_effects()
        self.assertEqual(prototype.value, 4)
        other = Player("Other", None)
        self.player.cast_spell(spell.id, other)
        self.assertIsNot(active, other.effects.get_by_stack_key("poison"))

    def test_noop_and_failed_extension_do_not_consume(self):
        class RejectedSpell(Spell):
            def apply(self, caster, target):
                return CastResult(False, "Тестовый отказ")
        for spell in (test_spell(damage=0), RejectedSpell("test_reject", "TEST", damage=1,
                      damage_type=Damage_type.ASTRAL, cost=2, resource="mana")):
            self.player.add_scroll(spell)
            self.assertFalse(self.player.cast_spell(spell.id, self.target, one_shot=True).success)
            self.assertEqual(self.player.mana, 10)
            self.assertIn((spell, 1), self.player.spellbook.scrolls)

    def test_validation_and_conflicting_ids(self):
        for fields in ({"cost": -1}, {"resource": "gold"}, {"damage_type": None}, {"damage": -1}):
            with self.assertRaises(ValueError):
                test_spell(**fields)
        self.player.learn_spell(self.spell)
        with self.assertRaises(ValueError):
            self.player.learn_spell(test_spell(name="Conflicting"))
        for count in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                self.player.add_scroll(self.spell, count)

    def test_three_test_spells_are_granted_to_every_class_idempotently(self):
        expected = {"astral_spark", "venom_mark", "renewal"}
        self.assertEqual(set(SPELLS), expected)
        self.assertTrue(all(set(value) == expected for value in STARTING_SPELL_IDS.values()))
        for cls in CLASSES.values():
            player = Player("Hero", None, cls)
            self.assertEqual({spell.id for spell in player.spellbook.learned}, expected)
            player.apply_character_class(cls)
            self.assertEqual({spell.id for spell in player.spellbook.learned}, expected)
        with patch.dict(SPELLS, {self.spell.id: self.spell}), patch.dict(STARTING_SPELL_IDS, {"daredevil": (self.spell.id,)}):
            player = Player("Hero", None, CLASSES["daredevil"])
            player.apply_character_class(CLASSES["daredevil"])
            self.assertEqual(player.spellbook.learned, (self.spell,))
            self.assertEqual(player.spellbook.scrolls, ())
        self.assertEqual(Player("Other", None).spellbook.learned, ())

    def test_spell_state_survives_player_round_trip(self):
        self.player.learn_spell(self.spell)
        self.player.add_scroll(self.spell, 2)
        restored = pickle.loads(pickle.dumps(self.player))
        self.assertEqual(restored.spellbook.learned, (self.spell,))
        self.assertTrue(restored.cast_spell(self.spell.id, self.target, one_shot=True).success)
        self.assertEqual(restored.spellbook.scrolls, ((self.spell, 1),))
        self.assertEqual(self.player.spellbook.scrolls, ((self.spell, 2),))

    def test_battle_adapter_grants_magic_and_consumes_only_on_success(self):
        from battle import PlayerTurnState, create_player_turn_state, cast_spell_action, MAGIC_ACTION_KIND
        self.player.learn_spell(self.spell)
        self.assertIn(MAGIC_ACTION_KIND, create_player_turn_state(self.player).available_actions)
        state = PlayerTurnState({MAGIC_ACTION_KIND})
        result = cast_spell_action(self.player, None, self.spell.id, state, action=NON_ATTACK_ACTION)
        self.assertFalse(result.success)
        self.assertTrue(state.can_use(MAGIC_ACTION_KIND))
        self.assertTrue(cast_spell_action(self.player, self.target, self.spell.id, state, action=NON_ATTACK_ACTION).success)
        self.assertFalse(cast_spell_action(self.player, self.target, self.spell.id, state, action=NON_ATTACK_ACTION).success)
        self.assertEqual(self.player.mana, 7)

    def test_all_three_spell_types_work_through_battle_selection(self):
        from battle import create_player_turn_state, get_combat_spells, player_turn, MAGIC_ACTION_KIND

        def cast(spell_id, player, target):
            index = next(i for i, (spell, _one_shot) in enumerate(get_combat_spells(player), 1)
                         if spell.id == spell_id)
            state = create_player_turn_state(player)
            with patch("battle.input", side_effect=["4", str(index)]), \
                    patch("battle.show_battle_screen"):
                messages = player_turn(player, target, [], state)
            self.assertFalse(state.can_use(MAGIC_ACTION_KIND))
            return messages

        attacker = Player("Mage", None)
        attacker.intelligence = 2
        attacker.learn_spell(SPELLS["astral_spark"])
        enemy = Player("Goblin", None)
        old_health = enemy.health
        messages = cast("astral_spark", attacker, enemy)
        self.assertEqual(enemy.health, old_health - 10)
        self.assertEqual(attacker.mana, 7)
        self.assertTrue(any("10 урона" in message for message in messages))

        caster = Player("Mage", None)
        caster.learn_spell(SPELLS["venom_mark"])
        enemy = Player("Goblin", None)
        messages = cast("venom_mark", caster, enemy)
        self.assertTrue(enemy.effects.contains(Poison))
        self.assertTrue(any("Яд" in message for message in messages))
        self.assertEqual(enemy.trigger_turn_start_effects().damage, 3)

        caster = Player("Mage", None)
        caster.learn_spell(SPELLS["renewal"])
        caster.health -= 10
        enemy = Player("Goblin", None)
        messages = cast("renewal", caster, enemy)
        self.assertTrue(caster.effects.contains(Regeneration))
        self.assertFalse(enemy.effects.contains(Regeneration))
        self.assertTrue(any("Регенерация" in message for message in messages))
        self.assertEqual(caster.trigger_turn_start_effects().health_restored, 4)

    def test_cancel_or_failed_spell_does_not_spend_magic_action(self):
        from battle import create_player_turn_state, player_turn, MAGIC_ACTION_KIND
        self.player.learn_spell(self.spell)
        for choices in (["4", "0"], ["4", "1"]):
            state = create_player_turn_state(self.player)
            self.player.mana = 0 if choices[-1] == "1" else 10
            with patch("battle.input", side_effect=choices), patch("battle.show_battle_screen"):
                player_turn(self.player, self.target, [], state)
            self.assertTrue(state.can_use(MAGIC_ACTION_KIND))


class TestSpellBookGUI(unittest.TestCase):
    def setUp(self):
        gc.collect()
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(str(exc))
        from gui import GameWindow
        self.app = GameWindow(self.root)
        from gui_views import character_snapshot
        self.player = Player("Hero", None)
        self.app.update_character(character_snapshot(self.player))
        from gui import Prompt
        self.app.show_prompt(Prompt("Действие", "battle", (("1", "Атака"),)))

    def tearDown(self):
        self.app.close()
        self.app = self.root = None
        gc.collect()

    def test_open_tabs_selection_refresh_and_close_preserve_game_prompt(self):
        from gui_views import character_snapshot
        prompt = self.app.prompt
        self.app.global_buttons["spellbook"].invoke()
        self.root.update()
        window = self.app.spellbook_window
        self.assertIsNotNone(window)
        self.assertEqual([window.notebook.tab(i, "text") for i in range(2)], ["Постоянные", "Одноразовые"])
        self.assertIn("Нет изученных", window.details.get("1.0", "end"))
        window.notebook.select(1)
        self.root.update()
        self.assertIn("Нет одноразовых", window.details.get("1.0", "end"))
        spell = test_spell(effects=(Poison(2),))
        self.player.learn_spell(spell)
        self.player.add_scroll(spell, 3)
        self.app.update_character(character_snapshot(self.player))
        self.root.update()
        self.assertEqual(window.lists["scrolls"].get(0), "TEST: удар ×3")
        details = window.details.get("1.0", "end")
        for text in ("3 MP", "10", "Яд", "Количество: 3", spell.description):
            self.assertIn(text, details)
        window.notebook.select(0)
        self.root.update()
        self.assertNotIn("Количество:", window.details.get("1.0", "end"))
        self.app.global_buttons["spellbook"].invoke()
        self.assertIs(self.app.spellbook_window, window)
        window.close_button.invoke()
        self.assertIsNone(self.app.spellbook_window)
        self.assertIs(self.app.prompt, prompt)
        self.assertTrue(self.app.waiting)
        self.assertTrue(self.app.io.answers.empty())
        self.assertEqual(self.player.mana, 10)

    def test_active_tab_uses_larger_visual_style(self):
        import tkinter.ttk as ttk
        style = ttk.Style(self.root)
        active_padding = style.lookup("SpellBook.TNotebook.Tab", "padding", ("selected",))
        inactive_padding = style.lookup("SpellBook.TNotebook.Tab", "padding", ("!selected",))
        active_font = style.lookup("SpellBook.TNotebook.Tab", "font", ("selected",))
        inactive_font = style.lookup("SpellBook.TNotebook.Tab", "font", ("!selected",))
        self.assertNotEqual(active_padding, inactive_padding)
        self.assertNotEqual(active_font, inactive_font)
