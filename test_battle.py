import unittest
from player import Player 
from enemy import Enemy 
from weapon import Weapon 
from damage import Damage_type
from objects import ITEMS, WEAPONS, create_item

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
        chest = create_item("leather_chest")
        player.inventory.add_item(chest)
        player.equip_armor(chest)

        player.take_damage(10)
        self.assertEqual(player.health, 30 - max(0, 10 - chest.defense))

        player.health = 30
        player.take_damage(1)
        self.assertEqual(player.health, 30)

        player.health = 30
        player.take_damage(10, Damage_type.MAGICAL)
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

    def test_dodge_is_not_applied_in_combat_yet(self):
        player = make_player()
        player.dexterity = 30
        player.health = 30
        player.take_damage(10)
        self.assertEqual(player.health, 20)

if __name__ == "__main__":
    unittest.main()