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

if __name__ == "__main__":
    unittest.main()