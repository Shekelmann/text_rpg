import unittest
from unittest.mock import Mock, patch

from affix_pool import WEAPON_AFFIX_POOL
from battle import player_turn, enemy_turn
from combat_hit import resolve_hit
from damage import Damage_type
from effects import Bleeding, Poison
from enemy import Enemy
from encounter import create_enemy
from player import Player
from test_dual_daggers import paired_player
from weapon import Weapon


class TestCombatHits(unittest.TestCase):
    def test_enemy_dodge_skips_roll_damage_and_on_hit_and_logs_miss(self):
        weapon = Weapon("Test", 10, 10, 0, "Одноручное", Damage_type.PHYSICAL,
                        affixes=(next(a for a in WEAPON_AFFIX_POOL if a.id == "poisonous"),))
        player = Player("Hero", weapon)
        enemy = Enemy("Dodger", 100, 1, 1, 0, Damage_type.PHYSICAL, dodge_chance=1)
        player.add_effect(Bleeding(2, 2))
        with patch("builtins.input", return_value="1"), \
             patch.object(player, "attack") as attack, \
             patch.object(enemy, "take_damage") as damage, \
             patch.object(weapon, "on_hit", wraps=weapon.on_hit) as on_hit:
            messages = player_turn(player, enemy)
        attack.assert_not_called()
        damage.assert_not_called()
        on_hit.assert_not_called()
        self.assertEqual(enemy.health, 100)
        self.assertFalse(enemy.effects.contains(Poison))
        self.assertTrue(any("уклоняется" in line for line in messages))
        self.assertEqual(player.health, player.max_health - 2)

    def test_hit_boundary_and_effect_order(self):
        enemy = Enemy("Target", 100, 1, 1, 0, Damage_type.PHYSICAL, dodge_chance=.2)
        effects = []
        result = resolve_hit(enemy, lambda: (20, True), Damage_type.PHYSICAL,
                             on_hit=lambda target: effects.append(target.health),
                             rng=Mock(random=Mock(return_value=.2)))
        self.assertTrue(result.hit)
        self.assertTrue(result.critical)
        self.assertEqual((result.damage, result.rolled_damage), (20, 20))
        self.assertEqual(effects, [80])

    def test_each_dagger_can_miss_independently(self):
        player = paired_player()
        enemy = Enemy("Target", 100, 1, 1, 0, Damage_type.PHYSICAL, dodge_chance=.5)
        with patch("builtins.input", return_value="1"), \
             patch("combat_hit.random.random", side_effect=[.1, .9]), \
             patch.object(player, "attack", return_value=(10, False)) as attack, \
             patch.object(player.main_hand, "on_hit") as first, \
             patch.object(player.off_hand, "on_hit") as second:
            messages = player_turn(player, enemy)
        self.assertEqual(enemy.health, 90)
        attack.assert_called_once_with(enemy, weapon=player.off_hand)
        first.assert_not_called()
        second.assert_called_once_with(enemy)
        self.assertTrue(any("уклоняется" in line for line in messages))

    def test_enemy_crit_is_rolled_and_doubles_base_damage(self):
        enemy = Enemy("Critical", 100, 10, 10, .2, Damage_type.PHYSICAL)
        with patch("enemy.random.random", return_value=.19):
            self.assertEqual(enemy.attack(), (20, True))
        with patch("enemy.random.random", return_value=.2):
            self.assertEqual(enemy.attack(), (10, False))

    def test_armor_reduces_already_critical_hit_and_log_uses_received_damage(self):
        player = Player("Hero", None)
        enemy = Enemy("Critical", 100, 10, 10, 1, Damage_type.PHYSICAL)
        with patch.object(player, "get_armor_defense", return_value=6):
            messages = enemy_turn(enemy, player)
        self.assertEqual(player.health, 106)  # 10 * 2 - 6, not (10 - 6) * 2
        self.assertIn("Critical наносит вам 14 урона.", messages)
        self.assertIn("Критический удар противника!", messages)

    def test_armor_floor_uses_full_critical_hit(self):
        player = Player("Hero", None)
        enemy = Enemy("Critical", 100, 11, 11, 1, Damage_type.PHYSICAL)
        with patch.object(player, "get_armor_defense", return_value=100):
            enemy_turn(enemy, player)
        self.assertEqual(player.health, 113)  # ceil(22 * .30)

    def test_astral_crit_uses_resistance_instead_of_armor(self):
        player = Player("Hero", None)
        player.set_resistance(Damage_type.ASTRAL, .5)
        enemy = Enemy("Critical", 100, 10, 10, 1, Damage_type.ASTRAL)
        with patch.object(player, "get_armor_defense", return_value=100):
            enemy_turn(enemy, player)
        self.assertEqual(player.health, 110)

    def test_player_dodge_does_not_log_enemy_crit(self):
        player = Player("Hero", None)
        enemy = Enemy("Critical", 100, 10, 10, 1, Damage_type.PHYSICAL)
        with patch.object(player, "get_dodge_chance", return_value=1), \
             patch.object(enemy, "attack") as attack:
            messages = enemy_turn(enemy, player)
        attack.assert_not_called()
        self.assertFalse(any("Критический" in line for line in messages))
        self.assertEqual(player.health, player.max_health)

    def test_species_dodge_is_preserved_across_scaling(self):
        wolf = create_enemy("wolf", 1)
        self.assertEqual(wolf.get_dodge_chance(), .12)
        wolf.scale_with_level(10, rarity="elite")
        self.assertEqual(wolf.get_dodge_chance(), .12)
        self.assertEqual(create_enemy("leshy", 1).get_dodge_chance(), 0)


if __name__ == "__main__":
    unittest.main()
