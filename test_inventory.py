import unittest

from affix_pool import WEAPON_AFFIX_POOL
from damage import Damage_type
from item import Armor, Inventory, Item
from item_presenter import item_icon_path, item_tooltip_lines
from rarity import Rarity
from weapon import Weapon


def named_item(name, item_type="material", rarity=Rarity.COMMON):
    return Item(name, item_type, use_in_combat=False, rarity=rarity)


class TestInventorySlots(unittest.TestCase):
    def test_default_inventory_has_twenty_real_slots(self):
        inventory = Inventory()

        self.assertEqual(inventory.size, 20)
        self.assertEqual(inventory.slots, (None,) * 20)
        self.assertEqual(inventory.items, [])

    def test_add_uses_first_empty_slot_and_preserves_positions(self):
        inventory = Inventory()
        first = named_item("Первый")
        second = named_item("Второй")

        self.assertTrue(inventory.add_item(first, slot=5))
        self.assertTrue(inventory.add_item(second))

        self.assertIs(inventory.item_at(5), first)
        self.assertIs(inventory.item_at(0), second)
        self.assertEqual(len(inventory.slots), 20)

    def test_full_inventory_rejects_another_item(self):
        inventory = Inventory()
        for index in range(20):
            self.assertTrue(inventory.add_item(named_item(str(index))))

        self.assertTrue(inventory.is_full())
        self.assertFalse(inventory.add_item(named_item("Лишний")))
        self.assertEqual(len(inventory.items), 20)

    def test_remove_leaves_empty_slot_in_place(self):
        inventory = Inventory()
        item = named_item("Предмет")
        inventory.add_item(item, slot=7)

        self.assertTrue(inventory.remove_item(item))

        self.assertIsNone(inventory.item_at(7))
        self.assertEqual(len(inventory.slots), 20)

    def test_move_to_empty_slot(self):
        inventory = Inventory()
        item = named_item("Предмет")
        inventory.add_item(item, slot=2)

        self.assertTrue(inventory.move_item(2, 14))

        self.assertIsNone(inventory.item_at(2))
        self.assertIs(inventory.item_at(14), item)

    def test_move_swaps_two_items(self):
        inventory = Inventory()
        first = named_item("Первый")
        second = named_item("Второй")
        inventory.add_item(first, slot=3)
        inventory.add_item(second, slot=9)

        self.assertTrue(inventory.move_item(3, 9))

        self.assertIs(inventory.item_at(3), second)
        self.assertIs(inventory.item_at(9), first)

    def test_slot_order_remains_after_other_reads(self):
        inventory = Inventory()
        item = named_item("Предмет")
        inventory.add_item(item, slot=11)
        saved = inventory.slots

        inventory.list_items()
        inventory.get_items_by_type("material")

        self.assertEqual(inventory.slots, saved)

    def test_sort_is_stable_by_type_rarity_and_name(self):
        inventory = Inventory()
        armor = Armor("Кираса", "body", 2)
        common_weapon = Weapon(
            "Меч", 1, 2, 0, "Одноручное", Damage_type.PHYSICAL,
            rarity=Rarity.COMMON,
        )
        rare_weapon = Weapon(
            "Топор", 1, 2, 0, "Одноручное", Damage_type.PHYSICAL,
            rarity=Rarity.RARE,
        )
        material = named_item("Шкура")
        for slot, item in ((10, material), (7, common_weapon), (4, armor), (1, rare_weapon)):
            inventory.add_item(item, slot=slot)

        inventory.sort_items()

        self.assertEqual(
            inventory.slots[:4],
            (rare_weapon, common_weapon, armor, material),
        )
        self.assertEqual(inventory.slots[4:], (None,) * 16)


class TestItemPresentation(unittest.TestCase):
    def test_missing_icon_returns_none(self):
        item = named_item("Паучья железа")

        self.assertIsNone(item_icon_path(item))

    def test_tooltip_omits_missing_optional_attributes(self):
        item = named_item("Паучья железа")

        lines = item_tooltip_lines(item)

        self.assertEqual(
            lines,
            ("Паучья железа", "Редкость: Обычный", "Тип: Материал"),
        )
        self.assertFalse(any("Урон" in line or "Броня" in line for line in lines))

    def test_weapon_tooltip_uses_existing_stats(self):
        weapon = Weapon(
            "Посох", 5, 9, 0.15, "Одноручное", Damage_type.ASTRAL,
            rarity=Rarity.RARE,
        )

        lines = item_tooltip_lines(weapon)

        self.assertIn("Урон: 5–9", lines)
        self.assertIn("Тип урона: Астральный урон", lines)
        self.assertIn("Критический удар: 15%", lines)

    def test_weapon_tooltip_includes_existing_dot_affix(self):
        poison_affix = next(
            affix for affix in WEAPON_AFFIX_POOL if affix.id == "poisonous"
        )
        weapon = Weapon(
            "Кинжал", 2, 4, 0.1, "Одноручное", Damage_type.PHYSICAL,
            rarity=Rarity.RARE,
            affixes=(poison_affix,),
        )

        lines = item_tooltip_lines(weapon)

        self.assertIn(
            "Ядовитый: При попадании накладывает 2 Poison (яд)",
            lines,
        )
        self.assertIn("Яд: 2", lines)


if __name__ == "__main__":
    unittest.main()
