import io
import random
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from unittest.mock import patch

from affix import AFFIX_COUNTS, AffixType
from affix_pool import WEAPON_AFFIX_POOL
from battle import player_turn
from character_class import CLASSES
from damage import Damage_type
from effects import ATTACK_ACTION, NON_ATTACK_ACTION, Bleeding, Poison
from enemy import Enemy
from interface import _show_category, _show_weapon_details, format_item_for_menu
from main import start_game
from objects import (
    CLASS_STARTING_WEAPON_POOLS,
    WEAPONS,
    create_item,
    generate_starting_weapon,
    generate_starting_weapons,
)
from player import Player
from rarity import Rarity
from weapon import Weapon


AFFIXES = {affix.id: affix for affix in WEAPON_AFFIX_POOL}


def make_weapon(*ids, damage_type=Damage_type.PHYSICAL):
    return Weapon("Меч", 20, 20, 0, "Двуручное", damage_type,
                  rarity=Rarity.EPIC, affixes=tuple(AFFIXES[id] for id in ids))


def make_enemy():
    return Enemy("Цель", 100, 1, 1, 0, Damage_type.PHYSICAL)


class TestPlayableAffixStats(unittest.TestCase):
    def attack(self, player, enemy):
        with patch("random.random", return_value=0.99):
            return player.attack(enemy)[0]

    def test_flat_damage_prefixes_preserve_base(self):
        for id, result in (("sharpened", 24), ("heavy", 28), ("light", 18)):
            item = make_weapon(id)
            self.assertEqual(item.get_damage_range(), (result, result))
            self.assertEqual((item.min_damage, item.max_damage), (20, 20))
        item = make_weapon("light")
        item.min_damage = item.max_damage = 1
        self.assertEqual(item.get_damage_range(), (0, 0))

    def test_dodge_is_relative_and_not_doubled_for_two_handed_weapon(self):
        for id, result in (("heavy", 0.12), ("light", 0.26)):
            item = make_weapon(id)
            player = Player("Hero", item)
            player.dexterity = 20
            self.assertIs(player.main_hand, player.off_hand)
            self.assertAlmostEqual(player.get_dodge_chance(), result)
            item.remove_affix(AFFIXES[id])
            self.assertAlmostEqual(player.get_dodge_chance(), 0.20)

    def test_dodge_stacks_additively_caps_and_disappears_on_unequip(self):
        player = Player("Hero", make_weapon("heavy", "light"))
        player.dexterity = 20
        self.assertAlmostEqual(player.get_dodge_chance(), 0.18)
        self.assertTrue(player.unequip_weapon())
        self.assertAlmostEqual(player.get_dodge_chance(), 0.20)
        player.inventory.add_item(make_weapon("light"))
        player.equip_weapon(player.inventory.items[-1])
        player.dexterity = 30
        self.assertEqual(player.get_dodge_chance(), 0.30)

    def test_assassin_strict_hp_boundary_rechecked_each_attack(self):
        player, enemy = Player("Hero", make_weapon("assassin")), make_enemy()
        player.strength = 10
        for hp, damage in ((20, 30), (19, 33), (21, 30), (1, 33)):
            enemy.health = hp
            self.assertEqual(self.attack(player, enemy), damage)

    def test_berserker_strict_boundary_includes_strength_and_rechecks(self):
        player, enemy = Player("Hero", make_weapon("berserker")), make_enemy()
        player.max_health = 100
        player.strength = 10
        for hp, damage in ((30, 30), (29, 36), (31, 30)):
            player.health = hp
            self.assertEqual(self.attack(player, enemy), damage)

    def test_status_conditions_ignore_expired_effects(self):
        for id, factory in (("poisoner", lambda: Poison(2)),
                            ("bloodletter", lambda: Bleeding(2, 2))):
            player, enemy = Player("Hero", make_weapon(id)), make_enemy()
            self.assertEqual(self.attack(player, enemy), 20)
            effect = enemy.add_effect(factory())
            self.assertEqual(self.attack(player, enemy), 24)
            if isinstance(effect, Poison):
                effect.value = 0
            else:
                effect.triggers = 0
            self.assertEqual(self.attack(player, enemy), 20)

    def test_multiple_conditions_add_percent_after_flat(self):
        item = make_weapon("sharpened", "heavy", "poisoner", "bloodletter")
        player, enemy = Player("Hero", item), make_enemy()
        enemy.add_effect(Poison(2))
        enemy.add_effect(Bleeding(2, 2))
        self.assertEqual(self.attack(player, enemy), 44)  # floor((20 + 4 + 8) * 1.4)
        self.assertEqual(item.final_min_damage, 32)  # context-free preview

    def test_conditional_physical_bonuses_do_not_apply_to_astral(self):
        item = make_weapon("heavy", "berserker", "poisoner", damage_type=Damage_type.ASTRAL)
        player, enemy = Player("Hero", item), make_enemy()
        player.health = 1
        player.intelligence = 5
        enemy.add_effect(Poison(2))
        self.assertEqual(self.attack(player, enemy), 25)

    def test_duelist_adds_percentage_points_and_obeys_player_cap(self):
        item = make_weapon("duelist")
        item.crit_chance = 0.15
        player = Player("Hero", item)
        self.assertAlmostEqual(item.final_crit_chance, 0.25)
        with patch("random.random", return_value=0.24):
            self.assertEqual(player.attack(make_enemy()), (40, True))
        player.dexterity = 20
        with patch("random.random", return_value=0.31):
            self.assertEqual(player.attack(make_enemy()), (20, False))

    def test_renaming_and_description_changes_do_not_affect_behavior(self):
        item = make_weapon("heavy", "poisonous", "assassin")
        item.set_affixes(tuple(replace(a, name="Другое", description="Другой текст")
                               for a in item.affixes))
        player, enemy = Player("Hero", item), make_enemy()
        enemy.health = 19
        self.assertEqual(self.attack(player, enemy), 32)
        item.on_hit(enemy)
        self.assertTrue(enemy.effects.contains(Poison))


class TestOnHitAffixes(unittest.TestCase):
    def hit(self, player, enemy):
        with patch("builtins.input", return_value="1"), patch("random.random", return_value=0.99):
            player_turn(player, enemy)

    def test_damage_rolls_and_failed_hits_do_not_apply_status(self):
        item = make_weapon("poisonous", "serrated")
        player, enemy = Player("Hero", item), make_enemy()
        player.attack(enemy)
        item.on_hit(enemy, successful=False)
        self.assertEqual(enemy.effects.effects, [])

    def test_successful_hit_applies_both_statuses_with_exact_values(self):
        player, enemy = Player("Hero", make_weapon("poisonous", "serrated")), make_enemy()
        player.intelligence = 100  # The requested fixed effects have no stat scaling.
        self.hit(player, enemy)
        self.assertEqual(enemy.health, 80)
        self.assertEqual(enemy.effects.get_by_stack_key("poison").value, 2)
        bleed = next(e for e in enemy.effects.effects if isinstance(e, Bleeding))
        self.assertEqual((bleed.damage, bleed.triggers), (2, 2))
        self.assertEqual(enemy.trigger_turn_start_effects().damage, 2)
        self.assertEqual(enemy.trigger_action_effects(NON_ATTACK_ACTION).damage, 0)
        self.assertEqual(enemy.trigger_action_effects(ATTACK_ACTION).damage, 2)
        self.assertEqual(enemy.trigger_action_effects(ATTACK_ACTION).damage, 2)
        self.assertEqual(enemy.trigger_action_effects(ATTACK_ACTION).damage, 0)
        self.assertEqual(enemy.trigger_turn_start_effects().damage, 1)
        self.assertFalse(enemy.effects.contains(Poison))

    def test_new_status_does_not_buff_the_hit_that_applied_it(self):
        for prefix, suffix in (("poisonous", "poisoner"), ("serrated", "bloodletter")):
            player, enemy = Player("Hero", make_weapon(prefix, suffix)), make_enemy()
            self.hit(player, enemy)
            self.assertEqual(enemy.health, 80)
            self.hit(player, enemy)
            self.assertEqual(enemy.health, 56)

    def test_hp_condition_uses_health_before_direct_damage(self):
        player, enemy = Player("Hero", make_weapon("assassin")), make_enemy()
        enemy.health = 25
        self.hit(player, enemy)
        self.assertEqual(enemy.health, 5)

    def test_repeated_hits_follow_existing_stacking_and_use_fresh_instances(self):
        item = make_weapon("poisonous", "serrated")
        first, second = make_enemy(), make_enemy()
        item.on_hit(first)
        item.on_hit(first)
        item.on_hit(second)
        self.assertEqual(first.effects.get_by_stack_key("poison").value, 4)
        self.assertEqual(second.effects.get_by_stack_key("poison").value, 2)
        bleeds = [e for e in first.effects.effects if isinstance(e, Bleeding)]
        self.assertEqual(len(bleeds), 2)
        self.assertIsNot(bleeds[0], bleeds[1])
        self.assertEqual(first.trigger_action_effects(ATTACK_ACTION).damage, 4)

    def test_skip_does_not_apply_on_hit_effects(self):
        player, enemy = Player("Hero", make_weapon("poisonous", "serrated")), make_enemy()
        with patch("builtins.input", return_value="2"):
            player_turn(player, enemy)
        self.assertEqual(enemy.effects.effects, [])


class TestStartingWeaponsAndUI(unittest.TestCase):
    def test_each_class_uses_only_its_starting_pool(self):
        for class_id, pool in CLASS_STARTING_WEAPON_POOLS.items():
            generated_ids = set()
            for seed in range(200):
                item = generate_starting_weapon(CLASSES[class_id], random.Random(seed))
                generated_ids.add(item.icon_id)
                self.assertIn(item.icon_id, pool)
            self.assertEqual(generated_ids, set(pool))

    def test_starting_weapon_uses_existing_rarity_and_affix_generation(self):
        rarities = set()
        for seed in range(200):
            item = generate_starting_weapon(CLASSES["herald"], random.Random(seed))
            rarities.add(item.rarity)
            low, high = AFFIX_COUNTS[item.rarity]
            self.assertTrue(low <= len(item.affixes) <= high)
            for kind in AffixType:
                self.assertLessEqual(sum(a.type == kind for a in item.affixes), 2)
            self.assertEqual(len({a.id for a in item.affixes}), len(item.affixes))
            self.assertTrue(all(a in WEAPON_AFFIX_POOL for a in item.affixes))
        self.assertEqual(rarities, set(AFFIX_COUNTS))

    def test_starting_generation_is_reproducible_and_templates_unchanged(self):
        first = generate_starting_weapon(CLASSES["bruiser"], random.Random(7))
        second = generate_starting_weapon(CLASSES["bruiser"], random.Random(7))
        self.assertEqual((first.name, first.rarity, first.affixes),
                         (second.name, second.rarity, second.affixes))
        first.min_damage = 999
        first.set_affixes(())
        self.assertNotEqual(second.min_damage, 999)
        self.assertTrue(all(i.affixes == () for i in WEAPONS.values()))
        self.assertEqual(create_item("sword").affixes, ())

    def test_three_starting_weapons_are_independent_class_items(self):
        for class_id, character_class in CLASSES.items():
            weapons = generate_starting_weapons(character_class, random.Random(11))

            self.assertEqual(len(weapons), 3)
            self.assertEqual(len({id(weapon) for weapon in weapons}), 3)
            self.assertTrue(all(
                weapon.icon_id in CLASS_STARTING_WEAPON_POOLS[class_id]
                for weapon in weapons
            ))
            first_other_damage = weapons[1].min_damage
            weapons[0].min_damage = 999
            self.assertEqual(weapons[1].min_damage, first_other_damage)

    def test_two_handed_starting_weapon_occupies_both_hands(self):
        with patch.dict(
            CLASS_STARTING_WEAPON_POOLS,
            {"bruiser": ("axe_2h",)},
        ):
            weapon = generate_starting_weapon(CLASSES["bruiser"], random.Random(3))
        player = Player("Hero", weapon, CLASSES["bruiser"])

        self.assertIs(player.main_hand, weapon)
        self.assertIs(player.off_hand, weapon)

    def test_new_game_equips_one_and_stores_two_generated_class_weapons(self):
        players = []
        with patch("builtins.input", side_effect=["Hero", "1"]), \
             patch("main.choose_character_class", return_value=CLASSES["bruiser"]), \
             patch("main.get_location_menu_options", return_value=[("exit", "Выход")]), \
             patch("main.clear"), \
             patch("main.show_player_status", side_effect=players.append), \
             redirect_stdout(io.StringIO()):
            start_game()
        self.assertEqual(len(players), 1)
        self.assertIsNotNone(players[0].main_hand)
        self.assertIn(players[0].main_hand.icon_id, CLASS_STARTING_WEAPON_POOLS["bruiser"])
        inventory_weapons = players[0].inventory.get_weapons()
        self.assertEqual(len(inventory_weapons), 2)
        self.assertTrue(all(
            weapon.icon_id in CLASS_STARTING_WEAPON_POOLS["bruiser"]
            for weapon in inventory_weapons
        ))
        self.assertEqual(len({id(players[0].main_hand), *(id(item) for item in inventory_weapons)}), 3)

    def test_display_name_and_descriptions_in_list_and_details(self):
        item = make_weapon("sharpened", "bloodletter")
        self.assertEqual(item.display_name, "Заточенный меч Кровопускателя")
        self.assertIn("Заточенный меч Кровопускателя", format_item_for_menu(item))
        player = Player("Hero", None)
        player.inventory.add_item(item)
        for show in (lambda: _show_category(player, "weapon", "Оружие"),
                     lambda: _show_weapon_details(item, False)):
            output = io.StringIO()
            with redirect_stdout(output), patch("builtins.input", return_value="0"):
                show()
            for affix in item.affixes:
                self.assertIn(f"{affix.name}: {affix.description}", output.getvalue())
            self.assertIn("24–24", output.getvalue())
        self.assertEqual(item.name, "Меч")


if __name__ == "__main__":
    unittest.main()
