import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch
from player import Player 
from enemy import Enemy 
from weapon import Weapon 
from damage import Damage_type
from objects import ITEMS, WEAPONS, create_item
from battle import battle, enemy_turn, player_turn, show_messages
from interface import allocate_stat_points, show_battle_screen, show_player_status

def make_player(name="Hero"):
    weapon = Weapon(
        "Меч",
        2,
        5,
        0.1,
        "Одноручное",
        Damage_type.PHYSICAL
    )
    return Player(name, weapon)

class TestBattle(unittest.TestCase):
    def test_battle_basic(self):
        player = make_player()

        enemy = Enemy(
            "Goblin",
            10,
            1,
            3,
            0.05,
            Damage_type.PHYSICAL
        )

        self.assertTrue(player.health > 0)
        self.assertTrue(enemy.health > 0)

    @patch("interface.clear")
    def test_battle_screen_shows_combat_state(self, mock_clear):
        player = make_player("Hero")
        player.health = 20
        player.mana = 7
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)
        enemy.health = 6

        output = io.StringIO()
        with redirect_stdout(output):
            show_battle_screen(player, enemy, ["Проверка сообщения."])

        screen = output.getvalue()
        mock_clear.assert_called_once_with()
        self.assertIn("Противник: Goblin", screen)
        self.assertIn("HP: 6 / 10", screen)
        self.assertIn("Игрок: Hero", screen)
        self.assertIn("HP: 20 / 30", screen)
        self.assertIn("Мана: 7 / 10", screen)
        self.assertIn("1 - Атака", screen)
        self.assertIn("Проверка сообщения.", screen)

    def test_critical_player_attack_returns_messages_in_reading_order(self):
        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch("builtins.input", return_value="1"), patch.object(
            player, "attack", return_value=(8, True)
        ):
            messages = player_turn(player, enemy)

        self.assertEqual(enemy.health, 2)
        self.assertEqual(
            messages,
            [
                "Вы наносите противнику «Goblin» 8 урона.",
                "Критический удар!",
            ],
        )

    def test_enemy_attack_returns_readable_message(self):
        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch.object(enemy, "attack", return_value=4), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(player.health, 26)
        self.assertEqual(messages, ["Goblin наносит вам 4 урона."])

    def test_successful_dodge_avoids_all_damage(self):
        player = make_player()
        player.dexterity = 10
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch.object(enemy, "attack", return_value=10), patch(
            "battle.random.random", return_value=0.09
        ), patch.object(player, "take_damage") as mock_take_damage:
            messages = enemy_turn(enemy, player)

        mock_take_damage.assert_not_called()
        self.assertEqual(player.health, player.max_health)
        self.assertEqual(messages, ["Вы уклоняетесь от атаки «Goblin»."])

    def test_failed_dodge_processes_attack_normally(self):
        player = make_player()
        player.dexterity = 10
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch.object(enemy, "attack", return_value=4), patch(
            "battle.random.random", return_value=0.10
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(player.health, 26)
        self.assertEqual(messages, ["Goblin наносит вам 4 урона."])

    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_combat_messages_are_shown_one_at_a_time(
        self,
        mock_screen,
        mock_sleep,
    ):
        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)
        rendered_logs = []
        mock_screen.side_effect = (
            lambda _player, _enemy, messages: rendered_logs.append(messages.copy())
        )

        messages = []
        show_messages(
            player,
            enemy,
            messages,
            ["Вы наносите 8 урона.", "Критический удар!"],
        )

        self.assertEqual(
            rendered_logs,
            [
                ["Вы наносите 8 урона."],
                ["Вы наносите 8 урона.", "Критический удар!"],
            ],
        )
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("battle.generate_loot", return_value=[])
    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_battle_returns_true_after_victory(
        self,
        _mock_screen,
        _mock_sleep,
        _mock_loot,
    ):
        player = make_player()
        enemy = Enemy("Goblin", 1, 1, 1, 0, Damage_type.PHYSICAL)

        with patch.object(player, "attack", return_value=(2, False)), patch(
            "builtins.input", side_effect=["1", ""]
        ):
            result = battle(player, enemy)

        self.assertTrue(result)

    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_battle_returns_false_after_defeat(
        self,
        _mock_screen,
        _mock_sleep,
    ):
        player = make_player()
        player.health = 1
        enemy = Enemy("Goblin", 10, 2, 2, 0, Damage_type.PHYSICAL)

        with patch("builtins.input", return_value="2"), patch.object(
            player, "after_death"
        ) as mock_after_death:
            result = battle(player, enemy)

        self.assertFalse(result)
        mock_after_death.assert_called_once_with()

class TestExperience(unittest.TestCase):
    def test_add_exp_accumulates(self):
        player = make_player()
        player.add_exp(10)
        player.add_exp(15)
        self.assertEqual(player.exp, 25)
        self.assertEqual(player.level, 1)
        self.assertEqual(player.exp_to_level, 100)

    def test_add_exp_does_not_replace_current(self):
        player = make_player()
        player.exp = 40
        player.add_exp(20)
        self.assertEqual(player.exp, 60)

    def test_level_up_at_threshold(self):
        player = make_player()
        player.add_exp(100)
        self.assertEqual(player.level, 2)
        self.assertEqual(player.exp, 0)
        self.assertEqual(player.exp_to_level, 125)

    def test_level_up_keeps_remainder(self):
        player = make_player()
        player.add_exp(110)
        self.assertEqual(player.level, 2)
        self.assertEqual(player.exp, 10)
        self.assertEqual(player.exp_to_level, 125)

    def test_multiple_level_ups(self):
        player = make_player()
        player.add_exp(225)
        self.assertEqual(player.level, 3)
        self.assertEqual(player.exp, 0)
        self.assertEqual(player.exp_to_level, 156)

    def test_level_up_restores_health(self):
        player = make_player()
        player.health = 1
        player.add_exp(100)
        self.assertEqual(player.max_health, round(30 * 1.1))
        self.assertEqual(player.health, player.max_health)

    def test_exp_requirement_uses_later_multipliers(self):
        player = make_player()
        player.level = 10
        player.exp = 0
        player.exp_to_level = 200
        player.add_exp(200)
        self.assertEqual(player.level, 11)
        self.assertEqual(player.exp_to_level, int(200 * 1.15))

class TestItems(unittest.TestCase):
    def test_create_item_returns_independent_instances(self):
        first = create_item("heal")
        second = create_item("heal")
        self.assertIsNot(first, second)
        self.assertIsNot(first, ITEMS["heal"])
        self.assertIsNot(second, ITEMS["heal"])

        sword_a = create_item("sword")
        sword_b = create_item("sword")
        self.assertIsNot(sword_a, sword_b)
        self.assertIsNot(sword_a, ITEMS["sword"])
        self.assertEqual(sword_a.name, ITEMS["sword"].name)
        self.assertEqual(sword_a.min_damage, ITEMS["sword"].min_damage)
        self.assertEqual(sword_a.max_damage, ITEMS["sword"].max_damage)
        self.assertEqual(sword_a.crit_chance, ITEMS["sword"].crit_chance)
        self.assertEqual(sword_a.weapon_type, ITEMS["sword"].weapon_type)
        self.assertEqual(sword_a.damage_type, ITEMS["sword"].damage_type)

    def test_changing_instance_does_not_change_catalog(self):
        template_damage = ITEMS["sword"].min_damage
        template_heal = ITEMS["heal"].heal
        catalog_sword = ITEMS["sword"]
        catalog_heal = ITEMS["heal"]

        sword = create_item("sword")
        potion = create_item("heal")
        sword.min_damage = 999
        potion.heal = 1

        self.assertIs(ITEMS["sword"], catalog_sword)
        self.assertIs(ITEMS["heal"], catalog_heal)
        self.assertEqual(ITEMS["sword"].min_damage, template_damage)
        self.assertEqual(ITEMS["heal"].heal, template_heal)
        self.assertEqual(WEAPONS["sword"].min_damage, template_damage)

    def test_two_looted_items_are_independent_inventory_entries(self):
        player = make_player()
        first = create_item("sword")
        second = create_item("sword")

        self.assertTrue(player.inventory.add_item(first))
        self.assertTrue(player.inventory.add_item(second))
        self.assertEqual(len(player.inventory.items), 2)
        self.assertIsNot(player.inventory.items[0], player.inventory.items[1])
        self.assertIsNot(player.inventory.items[0], ITEMS["sword"])
        self.assertIsNot(player.inventory.items[1], ITEMS["sword"])

        player.inventory.items[0].min_damage = 999
        self.assertEqual(player.inventory.items[1].min_damage, ITEMS["sword"].min_damage)

    def test_using_potion_removes_instance_not_catalog(self):
        player = make_player()
        player.health = 1
        catalog_heal = ITEMS["heal"]
        catalog_amount = catalog_heal.heal
        potion = create_item("heal")

        self.assertTrue(player.inventory.add_item(potion))
        self.assertTrue(potion.use(player))
        self.assertTrue(player.inventory.remove_item(potion))

        self.assertNotIn(potion, player.inventory.items)
        self.assertIs(ITEMS["heal"], catalog_heal)
        self.assertEqual(ITEMS["heal"].heal, catalog_amount)
        self.assertEqual(ITEMS["heal"].name, "Зелье лечения")

class TestEquipment(unittest.TestCase):
    def test_equip_one_handed_weapon(self):
        player = make_player()
        starter = player.main_hand
        sword = create_item("sword")
        player.inventory.add_item(sword)

        self.assertTrue(player.equip_weapon(sword))
        self.assertIs(player.main_hand, sword)
        self.assertIsNone(player.off_hand)
        self.assertNotIn(sword, player.inventory.items)
        self.assertIn(starter, player.inventory.items)

    def test_equip_two_handed_weapon(self):
        player = make_player()
        two_handed = create_item("2 handed sword")
        player.inventory.add_item(two_handed)

        self.assertTrue(player.equip_weapon(two_handed))
        self.assertIs(player.main_hand, two_handed)
        self.assertIs(player.off_hand, two_handed)
        self.assertNotIn(two_handed, player.inventory.items)

    def test_cannot_occupy_off_hand_while_two_handed_equipped(self):
        player = make_player()
        two_handed = create_item("2 handed sword")
        dagger = create_item("dagger")
        player.inventory.add_item(two_handed)
        player.inventory.add_item(dagger)

        self.assertTrue(player.equip_weapon(two_handed))
        self.assertFalse(player.equip_weapon(dagger, slot="off_hand"))
        self.assertIs(player.main_hand, two_handed)
        self.assertIs(player.off_hand, two_handed)
        self.assertIn(dagger, player.inventory.items)
        self.assertFalse(player.unequip_weapon(slot="off_hand"))
        self.assertIs(player.off_hand, two_handed)

    def test_unequip_weapon_returns_to_inventory(self):
        player = make_player()
        two_handed = create_item("2 handed sword")
        player.inventory.add_item(two_handed)
        player.equip_weapon(two_handed)

        self.assertTrue(player.unequip_weapon())
        self.assertIsNone(player.main_hand)
        self.assertIsNone(player.off_hand)
        self.assertEqual(player.inventory.items.count(two_handed), 1)
        self.assertIn(two_handed, player.inventory.items)

    def test_attack_uses_equipped_main_hand_weapon(self):
        player = make_player()
        player.unequip_weapon()
        weapon = Weapon(
            "Тестовый меч",
            5,
            5,
            0,
            "Одноручное",
            Damage_type.PHYSICAL
        )
        player.inventory.add_item(weapon)

        self.assertTrue(player.equip_weapon(weapon))
        damage, crit = player.attack()
        self.assertEqual(damage, 5)
        self.assertFalse(crit)
        self.assertIs(player.main_hand, weapon)

class TestArmor(unittest.TestCase):
    def test_armor_slots_are_separate(self):
        player = make_player()
        helmet = create_item("leather_helmet")
        chest = create_item("leather_chest")
        gloves = create_item("leather_gloves")
        boots = create_item("leather_boots")
        for piece in (helmet, chest, gloves, boots):
            player.inventory.add_item(piece)

        self.assertTrue(player.equip_armor(helmet))
        self.assertTrue(player.equip_armor(chest))
        self.assertTrue(player.equip_armor(gloves))
        self.assertTrue(player.equip_armor(boots))

        self.assertIs(player.head, helmet)
        self.assertIs(player.body, chest)
        self.assertIs(player.hands, gloves)
        self.assertIs(player.legs, boots)

    def test_equip_and_unequip_armor(self):
        player = make_player()
        helmet = create_item("leather_helmet")
        player.inventory.add_item(helmet)

        self.assertTrue(player.equip_armor(helmet))
        self.assertIs(player.head, helmet)
        self.assertNotIn(helmet, player.inventory.items)

        self.assertTrue(player.unequip_armor("head"))
        self.assertIsNone(player.head)
        self.assertIn(helmet, player.inventory.items)
        self.assertEqual(player.inventory.items.count(helmet), 1)

    def test_total_armor_defense_sums_equipped_pieces(self):
        player = make_player()
        helmet = create_item("leather_helmet")
        chest = create_item("leather_chest")
        player.inventory.add_item(helmet)
        player.inventory.add_item(chest)

        self.assertEqual(player.get_armor_defense(), 0)
        player.equip_armor(helmet)
        player.equip_armor(chest)
        self.assertEqual(player.get_armor_defense(), helmet.defense + chest.defense)

    def test_armor_reduces_physical_damage(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=5):
            player.take_damage(20, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 15)

    def test_armor_greater_than_incoming_damage_still_allows_damage(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=20):
            player.take_damage(10, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 27)

    def test_physical_damage_floor_is_thirty_percent_rounded_up(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=20):
            player.take_damage(11, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 26)

    def test_armor_damage_floor_does_not_affect_astral_damage(self):
        player = make_player()
        enemy = Enemy("Wraith", 10, 10, 10, 0, Damage_type.ASTRAL)
        with patch.object(player, "get_armor_defense", return_value=20), patch(
            "battle.random.random", return_value=1.0
        ):
            enemy_turn(enemy, player)

        self.assertEqual(player.health, 20)


    def test_replacing_armor_does_not_duplicate_items(self):
        player = make_player()
        first = create_item("leather_helmet")
        second = create_item("leather_helmet")
        player.inventory.add_item(first)
        player.inventory.add_item(second)

        self.assertTrue(player.equip_armor(first))
        self.assertTrue(player.equip_armor(second))

        self.assertIs(player.head, second)
        self.assertIn(first, player.inventory.items)
        self.assertNotIn(second, player.inventory.items)
        self.assertEqual(player.inventory.items.count(first), 1)
        self.assertEqual(player.inventory.items.count(second), 0)

        equipped_and_stored = player.inventory.items + [player.head]
        self.assertEqual(equipped_and_stored.count(first), 1)
        self.assertEqual(equipped_and_stored.count(second), 1)

    def test_equipped_armor_is_marked_in_category_list(self):
        from interface import _category_entries

        player = make_player()
        helmet = create_item("leather_helmet")
        chest = create_item("leather_chest")
        player.inventory.add_item(helmet)
        player.inventory.add_item(chest)
        player.equip_armor(helmet)

        entries = _category_entries(player, "armor")
        self.assertEqual(entries[0], ("equipped", helmet))
        self.assertEqual(entries[1], ("inventory", chest))


class TestResistances(unittest.TestCase):
    def test_astral_resistance_reduces_astral_damage_by_percentage(self):
        player = make_player()
        self.assertTrue(player.set_resistance(Damage_type.ASTRAL, 0.20))

        player.take_damage(10, Damage_type.ASTRAL)

        self.assertEqual(player.health, 22)

    def test_elemental_resistance_reduces_elemental_damage_by_percentage(self):
        player = make_player()
        self.assertTrue(player.set_resistance(Damage_type.ELEMENTAL, 0.40))

        player.take_damage(10, Damage_type.ELEMENTAL)

        self.assertEqual(player.health, 24)

    def test_resistance_is_capped_at_seventy_percent(self):
        player = make_player()
        self.assertTrue(player.set_resistance(Damage_type.ASTRAL, 1.0))

        player.take_damage(10, Damage_type.ASTRAL)

        self.assertEqual(player.get_resistance(Damage_type.ASTRAL), 0.70)
        self.assertEqual(player.health, 27)

    def test_resistance_only_affects_its_matching_damage_type(self):
        player = make_player()
        player.set_resistance(Damage_type.ASTRAL, 0.50)

        player.take_damage(10, Damage_type.ELEMENTAL)

        self.assertEqual(player.health, 20)

    def test_physical_damage_has_no_resistance(self):
        player = make_player()
        self.assertFalse(player.set_resistance(Damage_type.PHYSICAL, 0.70))

        with patch.object(player, "get_armor_defense", return_value=0):
            player.take_damage(10, Damage_type.PHYSICAL)

        self.assertEqual(player.get_resistance(Damage_type.PHYSICAL), 0)
        self.assertEqual(player.health, 20)


class TestCharacterClass(unittest.TestCase):
    def test_class_applies_base_stats(self):
        from character_class import CLASSES

        player = Player("Hero", None, CLASSES["bruiser"])
        self.assertEqual(player.character_class.name, "Бугай")
        self.assertEqual(player.max_health, 30)
        self.assertEqual(player.health, 30)
        self.assertEqual(player.strength, 4)
        self.assertEqual(player.dexterity, 1)
        self.assertEqual(player.intelligence, 1)

        player = Player("Hero", None, CLASSES["daredevil"])
        self.assertEqual(player.max_health, 25)
        self.assertEqual(player.strength, 2)
        self.assertEqual(player.dexterity, 3)

        player = Player("Hero", None, CLASSES["herald"])
        self.assertEqual(player.max_health, 20)
        self.assertEqual(player.intelligence, 3)

    def test_stat_bonuses_and_caps(self):
        player = make_player()
        player.strength = 4
        player.dexterity = 50
        player.intelligence = 3

        self.assertEqual(player.get_physical_damage_bonus(), 4)
        self.assertEqual(player.get_crit_chance(0.2), 0.30)
        self.assertEqual(player.get_dodge_chance(), 0.30)
        self.assertEqual(player.get_magic_damage_bonus(), 3)
        self.assertEqual(player.get_dot_bonus(), 3)

    def test_strength_adds_physical_damage(self):
        player = make_player()
        player.unequip_weapon()
        weapon = Weapon(
            "Тестовый меч",
            5,
            5,
            0,
            "Одноручное",
            Damage_type.PHYSICAL
        )
        player.inventory.add_item(weapon)
        player.equip_weapon(weapon)
        player.strength = 4

        damage, crit = player.attack()
        self.assertEqual(damage, 9)
        self.assertFalse(crit)

    def test_take_damage_does_not_repeat_dodge_check(self):
        player = make_player()
        player.dexterity = 30
        player.health = 30
        player.take_damage(10)
        self.assertEqual(player.health, 20)

    def test_dodge_chance_scales_with_dexterity_and_caps_at_thirty_percent(self):
        player = make_player()

        player.dexterity = 12
        self.assertEqual(player.get_dodge_chance(), 0.12)

        player.dexterity = 30
        self.assertEqual(player.get_dodge_chance(), 0.30)

        player.dexterity = 100
        self.assertEqual(player.get_dodge_chance(), 0.30)

def make_fixed_weapon(damage_type, name="Тестовое оружие"):
    return Weapon(name, 5, 5, 0, "Одноручное", damage_type)

def equip_weapon(player, weapon):
    player.unequip_weapon()
    player.inventory.add_item(weapon)
    player.equip_weapon(weapon)

class TestDirectDamageScaling(unittest.TestCase):
    def test_strength_increases_physical_damage(self):
        player = make_player()
        equip_weapon(player, make_fixed_weapon(Damage_type.PHYSICAL))
        player.strength = 4
        player.intelligence = 10
        player.dexterity = 0

        damage, crit = player.attack()
        self.assertEqual(damage, 9)
        self.assertFalse(crit)

    def test_elemental_damage_type_is_reserved_without_stat_scaling(self):
        player = make_player()
        player.intelligence = 3

        self.assertEqual(
            player.get_direct_damage_bonus(Damage_type.ELEMENTAL),
            0,
        )

    def test_intelligence_increases_astral_damage(self):
        player = make_player()
        equip_weapon(player, make_fixed_weapon(Damage_type.ASTRAL))
        player.strength = 10
        player.intelligence = 6
        player.dexterity = 0

        damage, crit = player.attack()
        self.assertEqual(damage, 11)
        self.assertFalse(crit)

    def test_dexterity_does_not_affect_direct_damage(self):
        player = make_player()
        player.strength = 2
        player.intelligence = 3
        player.dexterity = 50

        self.assertEqual(player.get_direct_damage_bonus(Damage_type.PHYSICAL), player.strength)
        self.assertEqual(player.get_direct_damage_bonus(Damage_type.ASTRAL), player.intelligence)

        with patch("player.random.random", return_value=1.0):
            equip_weapon(player, make_fixed_weapon(Damage_type.PHYSICAL))
            physical, crit = player.attack()
            self.assertFalse(crit)
            self.assertEqual(physical, 7)

            equip_weapon(player, make_fixed_weapon(Damage_type.ASTRAL))
            astral, crit = player.attack()
            self.assertFalse(crit)
            self.assertEqual(astral, 8)

    def test_magical_damage_is_an_alias_for_astral_damage(self):
        self.assertIs(Damage_type.MAGICAL, Damage_type.ASTRAL)


class TestPlayerStatusScreen(unittest.TestCase):
    @patch("interface.show_box")
    def test_status_fields_are_grouped_in_required_order(self, mock_show_box):
        player = make_player("Hero")
        player.strength = 4
        player.dexterity = 2
        player.intelligence = 3
        player.gold = 7
        player.health = 21
        player.mana = 6
        player.level = 2
        player.exp = 15
        player.exp_to_level = 125

        with patch.object(player, "get_armor_defense", return_value=5):
            show_player_status(player)

        self.assertEqual(
            mock_show_box.call_args.args[0],
            [
                "Имя: Hero",
                "Класс: —",
                "Сила: 4",
                "Ловкость: 2",
                "Интеллект: 3",
                "Урон: 6–9",
                "Броня: 5",
                "Золото: 7",
                None,
                "HP: 21 / 30",
                "Мана: 6 / 10",
                "Уровень: 2",
                "Опыт: 15/125",
            ],
        )

class TestStatAllocationOnLevelUp(unittest.TestCase):
    def test_level_up_grants_stat_point(self):
        player = make_player()
        self.assertEqual(player.unspent_stat_points, 0)
        player.add_exp(100)
        self.assertEqual(player.level, 2)
        self.assertEqual(player.unspent_stat_points, 1)

    def test_allocate_stat_increases_chosen_stat(self):
        player = make_player()
        player.add_exp(100)
        self.assertTrue(player.allocate_stat("strength"))
        self.assertEqual(player.strength, 1)
        self.assertEqual(player.unspent_stat_points, 0)

    def test_any_of_three_stats_can_be_chosen(self):
        player = make_player()
        player.strength = 4
        player.dexterity = 1
        player.intelligence = 1
        player.unspent_stat_points = 3

        self.assertTrue(player.allocate_stat("strength"))
        self.assertTrue(player.allocate_stat("dexterity"))
        self.assertTrue(player.allocate_stat("intelligence"))
        self.assertEqual(player.strength, 5)
        self.assertEqual(player.dexterity, 2)
        self.assertEqual(player.intelligence, 2)
        self.assertEqual(player.unspent_stat_points, 0)

    def test_multiple_level_ups_grant_multiple_points(self):
        player = make_player()
        player.strength = 2
        player.dexterity = 3
        player.intelligence = 1
        player.add_exp(225)
        self.assertEqual(player.level, 3)
        self.assertEqual(player.unspent_stat_points, 2)

        self.assertTrue(player.allocate_stat("intelligence"))
        self.assertTrue(player.allocate_stat("dexterity"))
        self.assertEqual(player.intelligence, 2)
        self.assertEqual(player.dexterity, 4)
        self.assertEqual(player.strength, 2)
        self.assertEqual(player.unspent_stat_points, 0)

    def test_class_does_not_block_stat_allocation(self):
        from character_class import CLASSES

        player = Player("Hero", None, CLASSES["herald"])
        player.unspent_stat_points = 1
        self.assertTrue(player.allocate_stat("strength"))
        self.assertEqual(player.strength, CLASSES["herald"].strength + 1)

    @patch("builtins.input", side_effect=["1", "3"])
    def test_cli_allocates_chosen_stats(self, _mock_input):
        player = make_player()
        player.strength = 2
        player.intelligence = 1
        player.add_exp(225)
        allocate_stat_points(player)
        self.assertEqual(player.strength, 3)
        self.assertEqual(player.intelligence, 2)
        self.assertEqual(player.unspent_stat_points, 0)

if __name__ == "__main__":
    unittest.main()
