import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch
from player import Player 
from item import Item
from enemy import Enemy 
from weapon import Weapon 
from damage import Damage_type
from objects import ITEMS, WEAPONS, create_item
from battle import (
    ATTACK_ACTION_KIND,
    CONSUMABLE_ACTION_KIND,
    MAGIC_ACTION_KIND,
    PlayerTurnState,
    battle,
    create_player_turn_state,
    enemy_turn,
    get_player_turn_actions,
    player_turn,
    show_messages,
    finish_victory,
)
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
    def test_victory_shows_one_aggregated_reward_block(self):
        player = make_player()
        enemy = Enemy(
            "Goblin", 10, 1, 1, 0, Damage_type.PHYSICAL, exp_reward=17
        )
        enemy.gold = (5, 5)
        item = create_item("sword")
        messages = ["История боя."]

        with patch("battle.show_messages"), patch(
            "battle.allocate_stat_points"
        ), patch("battle.generate_loot", return_value=[item]), patch(
            "battle.show_battle_rewards"
        ) as reward, patch("builtins.input", return_value=""):
            self.assertTrue(finish_victory(player, enemy, messages))

        reward.assert_called_once_with(
            player, enemy, messages, 5, 17, [item]
        )
        self.assertIn("Получено золота: 5", messages)

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
        self.assertIn("HP: 20 / 120", screen)
        self.assertIn("Мана: 7 / 8", screen)
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

    def test_attack_cost_prevents_second_attack_with_three_action_points(self):
        player = make_player()
        enemy = Enemy("Goblin", 30, 1, 1, 0, Damage_type.PHYSICAL)
        turn_state = PlayerTurnState({ATTACK_ACTION_KIND, CONSUMABLE_ACTION_KIND})

        with patch("builtins.input", side_effect=["1", "1"]), patch.object(
            player, "attack", return_value=(5, False)
        ) as mock_attack:
            first_messages = player_turn(player, enemy, turn_state=turn_state)
            second_messages = player_turn(player, enemy, turn_state=turn_state)

        self.assertEqual(enemy.health, 25)
        self.assertEqual(mock_attack.call_count, 1)
        self.assertIn("5 урона", first_messages[0])
        self.assertEqual(
            second_messages,
            ["Недостаточно ОД."],
        )

    def test_consumables_can_be_used_repeatedly_while_action_points_remain(self):
        player = make_player()
        player.health = 20
        enemy = Enemy("Goblin", 30, 1, 1, 0, Damage_type.PHYSICAL)
        turn_state = create_player_turn_state(player)

        with patch("builtins.input", side_effect=["3", "1", "3", "1"]), patch(
            "battle.show_battle_screen"
        ):
            player_turn(player, enemy, turn_state=turn_state)
            messages = player_turn(player, enemy, turn_state=turn_state)

        self.assertEqual(player.current_hp_flasks, 1)
        self.assertIn("Вы используете", messages[0])
        self.assertEqual(turn_state.action_points, 1)

    def test_attack_spends_two_action_points(self):
        player = make_player()
        enemy = Enemy("Goblin", 30, 1, 1, 0, Damage_type.PHYSICAL)
        turn_state = create_player_turn_state(player)

        with patch("builtins.input", return_value="1"), patch.object(
            player, "attack", return_value=(5, False)
        ):
            player_turn(player, enemy, turn_state=turn_state)

        self.assertEqual(turn_state.action_points, 1)
        self.assertFalse(turn_state.is_complete)

    def test_finish_turn_ends_turn_with_unused_actions(self):
        turn_state = PlayerTurnState({ATTACK_ACTION_KIND, CONSUMABLE_ACTION_KIND})
        player = make_player()
        enemy = Enemy("Goblin", 30, 1, 1, 0, Damage_type.PHYSICAL)

        with patch("builtins.input", return_value="2"):
            messages = player_turn(player, enemy, turn_state=turn_state)

        self.assertTrue(turn_state.is_complete)
        self.assertEqual(messages, ["Вы завершаете ход."])

    def test_zero_cost_magic_does_not_spend_action_points(self):
        turn_state = PlayerTurnState({MAGIC_ACTION_KIND})

        self.assertTrue(turn_state.use(MAGIC_ACTION_KIND))
        self.assertTrue(turn_state.use(MAGIC_ACTION_KIND))
        self.assertEqual(turn_state.action_points, 3)
        self.assertFalse(turn_state.is_complete)

    def test_finish_turn_is_shown_while_actions_remain(self):
        turn_state = PlayerTurnState({ATTACK_ACTION_KIND, CONSUMABLE_ACTION_KIND})
        turn_state.use(ATTACK_ACTION_KIND)

        actions = get_player_turn_actions(turn_state)

        self.assertFalse(any("Атака" in action for action in actions))
        self.assertTrue(any("Использовать флягу — 1 ОД" in action for action in actions))
        self.assertIn("2 - Завершить ход", actions)

    @patch("battle.generate_loot", return_value=[])
    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_consumable_and_attack_can_be_used_once_before_enemy_turn(
        self,
        _mock_screen,
        _mock_sleep,
        _mock_loot,
    ):
        player = make_player()
        player.health = 20
        enemy = Enemy("Goblin", 1, 1, 1, 0, Damage_type.PHYSICAL)

        with patch.object(player, "attack", return_value=(2, False)), patch.object(
            enemy, "attack"
        ) as mock_enemy_attack, patch(
            "builtins.input", side_effect=["3", "1", "1", ""]
        ):
            result = battle(player, enemy)

        self.assertTrue(result)
        self.assertEqual(player.current_hp_flasks, 2)
        mock_enemy_attack.assert_not_called()

    @patch("battle.time.sleep")
    @patch("battle.show_battle_screen")
    def test_magic_shield_does_not_trigger_enemy_before_next_player_action(
        self,
        _mock_screen,
        _mock_sleep,
    ):
        from spells import SPELLS

        player = make_player()
        player.learn_spell(SPELLS["magic_shield"])
        enemy = Enemy("Goblin", 100, 1, 1, 0, Damage_type.PHYSICAL)
        action_order = []

        def player_attack(_target, weapon=None):
            action_order.append("player_attack")
            return 5, False

        def run_enemy_turn(_enemy, target):
            action_order.append("enemy_turn")
            target.health = 0
            return ["Enemy turn"]

        with patch.object(player, "attack", side_effect=player_attack), patch.object(
            player, "after_death"
        ), patch(
            "battle.enemy_turn", side_effect=run_enemy_turn
        ) as mock_enemy_turn, patch(
            "battle.input", side_effect=("4", "1", "1")
        ):
            result = battle(player, enemy)

        self.assertFalse(result)
        self.assertEqual(action_order, ["player_attack", "enemy_turn"])
        mock_enemy_turn.assert_called_once_with(enemy, player)

    def test_enemy_attack_returns_readable_message(self):
        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch.object(enemy, "attack", return_value=(4, False)), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(player.health, 116)
        self.assertEqual(messages, ["Goblin наносит вам 4 урона."])

    def test_enemy_hit_feedback_uses_damage_after_magic_shield(self):
        from effects import PhysicalShield

        player = make_player()
        player.add_effect(PhysicalShield())
        enemy = Enemy("Goblin", 10, 10, 10, 0, Damage_type.PHYSICAL)
        with patch.object(enemy, "attack", return_value=(10, False)), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(messages[0], "Магический щит: 10 → 7 (поглощено 3).")
        change = messages[1].health_changes[0]
        self.assertEqual((change.before, change.after, change.amount), (120, 113, 7))
        self.assertEqual(messages[1], "Goblin наносит вам 7 урона.")

    def test_magic_shield_log_and_health_event_match_after_armor(self):
        from effects import PhysicalShield

        player = make_player()
        player.add_effect(PhysicalShield())
        enemy = Enemy("Goblin", 10, 10, 10, 0, Damage_type.PHYSICAL)
        with patch.object(player, "get_armor_defense", return_value=20), patch.object(
            enemy, "attack", return_value=(10, False)
        ), patch("battle.random.random", return_value=1.0):
            messages = enemy_turn(enemy, player)

        self.assertEqual(messages[0], "Магический щит: 3 → 2 (поглощено 1).")
        change = messages[1].health_changes[0]
        self.assertEqual((change.amount, player.health), (2, 118))
        self.assertEqual(messages[1], "Goblin наносит вам 2 урона.")

    def test_enemy_attack_message_uses_damage_after_armor(self):
        player = make_player()
        enemy = Enemy("Goblin", 10, 10, 10, 0, Damage_type.PHYSICAL)

        with patch.object(player, "get_armor_defense", return_value=20), patch(
            "battle.random.random", return_value=1.0
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(player.health, 117)
        self.assertEqual(messages, ["Goblin наносит вам 3 урона."])

    def test_successful_dodge_avoids_all_damage(self):
        player = make_player()
        player.dexterity = 10
        enemy = Enemy("Goblin", 10, 1, 3, 0.05, Damage_type.PHYSICAL)

        with patch.object(enemy, "attack", return_value=(10, False)), patch(
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

        with patch.object(enemy, "attack", return_value=(4, False)), patch(
            "battle.random.random", return_value=0.10
        ):
            messages = enemy_turn(enemy, player)

        self.assertEqual(player.health, 116)
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

    def test_show_messages_forwards_visual_event_without_changing_log_text(self):
        from combat_feedback import damage_change, feedback_message

        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 1, 0, Damage_type.PHYSICAL)
        message = feedback_message(
            "Удар на 3.",
            damage_change(enemy, 10, 7, Damage_type.PHYSICAL),
        )
        history = []
        with patch("battle.show_battle_screen") as screen, patch(
            "battle.time.sleep"
        ):
            show_messages(player, enemy, history, [message])

        self.assertEqual(history, ["Удар на 3."])
        event = screen.call_args.kwargs["health_events"][0]
        self.assertEqual(
            (event["target"], event["before"], event["after"], event["amount"]),
            ("enemy", 10, 7, 3),
        )

    def test_battle_keeps_messages_from_all_turns_until_victory(self):
        player = make_player()
        enemy = Enemy("Goblin", 10, 1, 1, 0, Damage_type.PHYSICAL)
        player_turn_count = 0

        def scripted_player_turn(_player, target, _messages, turn_state):
            nonlocal player_turn_count
            player_turn_count += 1
            if player_turn_count == 1:
                turn_state.finish()
                return ["Первое действие игрока."]
            target.health = 0
            return ["Победное действие игрока."]

        with patch("battle.player_turn", side_effect=scripted_player_turn), patch(
            "battle.enemy_turn", return_value=["Действие врага."]
        ), patch("battle.show_battle_screen"), patch(
            "battle.time.sleep"
        ), patch("battle.finish_victory", return_value=True) as finish:
            self.assertTrue(battle(player, enemy))

        victory_messages = finish.call_args.args[2]
        self.assertEqual(victory_messages, [
            "Вы встретили противника «Goblin».",
            "Первое действие игрока.",
            "Действие врага.",
            "Победное действие игрока.",
        ])

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
        self.assertEqual(player.max_health, round(120 * 1.1))
        self.assertEqual(player.health, player.max_health)

    def test_level_up_preserves_class_health_difference(self):
        from character_class import CLASSES

        expected_health = {
            "bruiser": round(105 * 1.1) + 4 * 5,
            "daredevil": round(100 * 1.1) + 2 * 5,
            "herald": round(95 * 1.1) + 1 * 5,
        }

        for class_id, max_health in expected_health.items():
            with self.subTest(character_class=class_id):
                player = Player("Hero", None, CLASSES[class_id])
                player.level_up()
                self.assertEqual(player.max_health, max_health)
                self.assertEqual(player.health, max_health)

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
        catalog_sword = ITEMS["sword"]

        sword = create_item("sword")
        sword.min_damage = 999

        self.assertIs(ITEMS["sword"], catalog_sword)
        self.assertEqual(ITEMS["sword"].min_damage, template_damage)
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

    def test_removing_material_does_not_change_catalog(self):
        player = make_player()
        catalog_material = ITEMS["spider_gland"]
        material = create_item("spider_gland")

        self.assertTrue(player.inventory.add_item(material))
        self.assertTrue(player.inventory.remove_item(material))

        self.assertNotIn(material, player.inventory.items)
        self.assertIs(ITEMS["spider_gland"], catalog_material)

class TestEquipment(unittest.TestCase):
    def test_higher_level_weapon_unlocks_after_player_level_up(self):
        player = Player("Hero", None)
        weapon = create_item("sword")
        weapon.level = 2
        player.inventory.add_item(weapon)

        self.assertFalse(player.equip_weapon(weapon))
        self.assertIn(weapon, player.inventory.items)
        self.assertEqual(
            player.get_weapon_equip_error(weapon),
            "Требуется уровень 2. Ваш уровень: 1.",
        )

        player.level_up()

        self.assertTrue(player.equip_weapon(weapon))
        self.assertIs(player.main_hand, weapon)

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
        two_handed = create_item("2 handed axe")
        player.inventory.add_item(two_handed)

        self.assertTrue(player.equip_weapon(two_handed))
        self.assertIs(player.main_hand, two_handed)
        self.assertIs(player.off_hand, two_handed)
        self.assertNotIn(two_handed, player.inventory.items)

    def test_cannot_occupy_off_hand_while_two_handed_equipped(self):
        player = make_player()
        two_handed = create_item("2 handed axe")
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
        two_handed = create_item("2 handed axe")
        player.inventory.add_item(two_handed)
        player.equip_weapon(two_handed)

        self.assertTrue(player.unequip_weapon())
        self.assertIsNone(player.main_hand)
        self.assertIsNone(player.off_hand)
        self.assertEqual(player.inventory.items.count(two_handed), 1)
        self.assertIn(two_handed, player.inventory.items)

    def test_one_handed_staff_leaves_off_hand_free(self):
        player = make_player()
        staff = create_item("staff")
        player.inventory.add_item(staff)

        self.assertTrue(player.equip_weapon(staff))
        self.assertIs(player.main_hand, staff)
        self.assertIsNone(player.off_hand)

    def test_two_handed_staff_occupies_both_hands(self):
        player = make_player()
        staff = create_item("2 handed staff")
        player.inventory.add_item(staff)

        self.assertTrue(player.equip_weapon(staff))
        self.assertIs(player.main_hand, staff)
        self.assertIs(player.off_hand, staff)

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
    def test_armor_has_one_slot_and_replacement_returns_previous_item(self):
        player = make_player()
        first = create_item("leather_armor")
        second = create_item("leather_armor")
        for item in (first, second):
            player.inventory.add_item(item)
        self.assertTrue(player.equip_armor(first))
        self.assertTrue(player.equip_armor(second))
        self.assertIs(player.armor, second)
        self.assertEqual(player.inventory.items, [first])
        for removed_slot in ("head", "body", "hands", "legs"):
            self.assertFalse(hasattr(player, removed_slot))

    def test_equip_and_unequip_armor(self):
        player = make_player()
        helmet = create_item("leather_armor")
        player.inventory.add_item(helmet)

        self.assertTrue(player.equip_armor(helmet))
        self.assertIs(player.armor, helmet)
        self.assertNotIn(helmet, player.inventory.items)

        self.assertTrue(player.unequip_armor("armor"))
        self.assertIsNone(player.armor)
        self.assertIn(helmet, player.inventory.items)
        self.assertEqual(player.inventory.items.count(helmet), 1)

    def test_armor_defense_uses_only_current_armor(self):
        player = make_player()
        helmet = create_item("leather_armor")
        chest = create_item("leather_armor")
        chest.defense = 7
        player.inventory.add_item(helmet)
        player.inventory.add_item(chest)

        self.assertEqual(player.get_armor_defense(), 0)
        player.equip_armor(helmet)
        player.equip_armor(chest)
        self.assertEqual(player.get_armor_defense(), chest.defense)

    def test_accessory_can_be_replaced_and_unequipped_safely(self):
        player = make_player()
        first = Item("Первый амулет", "accessory", False)
        second = Item("Второй амулет", "accessory", False)
        first.slot = second.slot = "amulet"
        player.inventory.add_item(first)
        player.inventory.add_item(second)

        self.assertTrue(player.equip_accessory(first))
        self.assertTrue(player.equip_accessory(second))
        self.assertIs(player.amulet, second)
        self.assertIn(first, player.inventory.items)
        self.assertTrue(player.unequip_item("amulet"))
        self.assertIsNone(player.amulet)
        self.assertIn(second, player.inventory.items)

        player.equip_accessory(second)
        while not player.inventory.is_full():
            player.inventory.add_item(create_item("dagger"))
        self.assertFalse(player.unequip_item("amulet"))
        self.assertIs(player.amulet, second)

    def test_armor_reduces_physical_damage(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=5):
            received_damage = player.take_damage(20, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 105)
        self.assertEqual(received_damage, 15)

    def test_armor_greater_than_incoming_damage_still_allows_damage(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=20):
            player.take_damage(10, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 117)

    def test_physical_damage_floor_is_thirty_percent_rounded_up(self):
        player = make_player()
        with patch.object(player, "get_armor_defense", return_value=20):
            player.take_damage(11, Damage_type.PHYSICAL)

        self.assertEqual(player.health, 116)

    def test_armor_damage_floor_does_not_affect_astral_damage(self):
        player = make_player()
        enemy = Enemy("Wraith", 10, 10, 10, 0, Damage_type.ASTRAL)
        with patch.object(player, "get_armor_defense", return_value=20), patch(
            "battle.random.random", return_value=1.0
        ):
            enemy_turn(enemy, player)

        self.assertEqual(player.health, 110)


    def test_replacing_armor_does_not_duplicate_items(self):
        player = make_player()
        first = create_item("leather_armor")
        second = create_item("leather_armor")
        player.inventory.add_item(first)
        player.inventory.add_item(second)

        self.assertTrue(player.equip_armor(first))
        self.assertTrue(player.equip_armor(second))

        self.assertIs(player.armor, second)
        self.assertIn(first, player.inventory.items)
        self.assertNotIn(second, player.inventory.items)
        self.assertEqual(player.inventory.items.count(first), 1)
        self.assertEqual(player.inventory.items.count(second), 0)

        equipped_and_stored = player.inventory.items + [player.armor]
        self.assertEqual(equipped_and_stored.count(first), 1)
        self.assertEqual(equipped_and_stored.count(second), 1)

    def test_equipped_armor_is_marked_in_category_list(self):
        from interface import _category_entries

        player = make_player()
        helmet = create_item("leather_armor")
        chest = create_item("leather_armor")
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

        received_damage = player.take_damage(10, Damage_type.ASTRAL)

        self.assertEqual(player.health, 112)
        self.assertEqual(received_damage, 8)

    def test_take_damage_returns_actual_health_lost_on_overkill(self):
        player = make_player()
        player.health = 2

        received_damage = player.take_damage(10, Damage_type.ASTRAL)

        self.assertEqual(player.health, 0)
        self.assertEqual(received_damage, 2)

    def test_elemental_resistance_reduces_elemental_damage_by_percentage(self):
        player = make_player()
        self.assertTrue(player.set_resistance(Damage_type.ELEMENTAL, 0.40))

        player.take_damage(10, Damage_type.ELEMENTAL)

        self.assertEqual(player.health, 114)

    def test_resistance_is_capped_at_seventy_percent(self):
        player = make_player()
        self.assertTrue(player.set_resistance(Damage_type.ASTRAL, 1.0))

        player.take_damage(10, Damage_type.ASTRAL)

        self.assertEqual(player.get_resistance(Damage_type.ASTRAL), 0.70)
        self.assertEqual(player.health, 117)

    def test_resistance_only_affects_its_matching_damage_type(self):
        player = make_player()
        player.set_resistance(Damage_type.ASTRAL, 0.50)

        player.take_damage(10, Damage_type.ELEMENTAL)

        self.assertEqual(player.health, 110)

    def test_physical_damage_has_no_resistance(self):
        player = make_player()
        self.assertFalse(player.set_resistance(Damage_type.PHYSICAL, 0.70))

        with patch.object(player, "get_armor_defense", return_value=0):
            player.take_damage(10, Damage_type.PHYSICAL)

        self.assertEqual(player.get_resistance(Damage_type.PHYSICAL), 0)
        self.assertEqual(player.health, 110)


class TestCharacterClass(unittest.TestCase):
    def test_class_applies_base_stats(self):
        from character_class import CLASSES

        player = Player("Hero", None, CLASSES["bruiser"])
        self.assertEqual(player.character_class.name, "Бугай")
        self.assertEqual(player.max_health, 125)
        self.assertEqual(player.health, 125)
        self.assertEqual(player.strength, 4)
        self.assertEqual(player.dexterity, 1)
        self.assertEqual(player.intelligence, 1)

        player = Player("Hero", None, CLASSES["daredevil"])
        self.assertEqual(player.max_health, 110)
        self.assertEqual(player.strength, 2)
        self.assertEqual(player.dexterity, 3)

        player = Player("Hero", None, CLASSES["herald"])
        self.assertEqual(player.max_health, 100)
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
    def test_intelligence_updates_central_astral_damage_range(self):
        player = make_player()
        equip_weapon(player, create_item("2 handed staff"))
        player.intelligence = 3

        self.assertEqual(player.get_attack_damage_range(), (31, 55))

        player.unspent_stat_points = 1
        self.assertTrue(player.allocate_stat("intelligence"))
        self.assertEqual(player.get_attack_damage_range(), (32, 56))

    def test_astral_combat_roll_uses_updated_damage_range(self):
        player = make_player()
        equip_weapon(player, create_item("2 handed staff"))
        player.intelligence = 4

        with patch("player.random.randint", side_effect=lambda low, high: low) as roll, patch(
            "player.random.random", return_value=1.0
        ):
            damage, crit = player.attack()

        roll.assert_called_once_with(32, 56)
        self.assertEqual(damage, 32)
        self.assertFalse(crit)

    def test_gui_damage_range_uses_same_player_calculation(self):
        from gui_views import character_snapshot

        player = make_player()
        equip_weapon(player, create_item("2 handed staff"))
        player.intelligence = 4

        self.assertEqual(character_snapshot(player)["damage"], "32–56")

    @patch("battle.input", return_value="1")
    def test_staff_attack_keeps_astral_type_in_battle(self, _mock_input):
        player = make_player()
        staff = create_item("staff")
        equip_weapon(player, staff)
        enemy = Enemy("Target", 100, 0, 0, 0, Damage_type.PHYSICAL)

        with patch.object(player, "attack", return_value=(12, False)), patch.object(
            enemy,
            "take_damage",
            wraps=enemy.take_damage,
        ) as take_damage:
            messages = player_turn(player, enemy)

        take_damage.assert_called_once_with(12, Damage_type.ASTRAL)
        self.assertEqual(messages, ["Вы наносите противнику «Target» 12 урона."])

    def test_staff_attack_scales_with_int_and_uses_astral_mitigation(self):
        attacker = make_player()
        staff = create_item("staff")
        equip_weapon(attacker, staff)
        attacker.intelligence = 6
        defender = make_player()
        defender.set_resistance(Damage_type.ASTRAL, 0.25)

        with patch("player.random.randint", side_effect=lambda low, high: low), patch(
            "player.random.random", return_value=1.0
        ), patch.object(defender, "get_armor_defense", return_value=100):
            damage, crit = attacker.attack(defender)
            received = defender.take_damage(damage, staff.damage_type)

        self.assertFalse(crit)
        self.assertEqual(damage, 16)
        self.assertEqual(received, 12)

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
                "День 1",
                "Класс: —",
                "Сила: 4",
                "Ловкость: 2",
                "Интеллект: 3",
                "Урон: 6–9",
                "Броня: 5",
                "Золото: 7",
                None,
                "HP: 21 / 120",
                "Мана: 6 / 8",
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

    def test_strength_increases_max_health_and_preserves_missing_health(self):
        player = make_player()
        player.health = player.max_health - 7
        player.unspent_stat_points = 1
        old_max_health = player.max_health

        self.assertTrue(player.allocate_stat("strength"))

        self.assertEqual(player.max_health, old_max_health + 5)
        self.assertEqual(player.health, player.max_health - 7)

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
