from rarity import Rarity
from flasks import FlaskStock

#from weapon import Weapon

class Inventory:
    def __init__ (self, size = 20):
        self.size = size # Макс кол-во предметов
        self._slots = [None] * size
        self.flasks = {key: FlaskStock() for key in ("hp", "mp")}

    @property
    def slots(self):
        """Stable backpack positions exposed read-only to interface code."""
        return tuple(self._slots)

    @property
    def items(self):
        """Occupied items in slot order; compatibility for existing systems."""
        return [item for item in self._slots if item is not None]

    def is_full(self):
        return all(item is not None for item in self._slots)

    def add_item(self, item, slot=None): # Добавление предмета и проверка на заполненность инвентаря
        resource = getattr(item, "flask_resource", None)
        if resource in self.flasks:
            return self.flasks[resource].add(item)
        if item in self._slots:
            return False
        if slot is None:
            try:
                slot = self._slots.index(None)
            except ValueError:
                return False
        if not self._valid_slot(slot) or self._slots[slot] is not None:
            return False
        self._slots[slot] = item
        return True

    def remove_item(self, item): # Удаление предмета из инвентаря
        resource = getattr(item, "flask_resource", None)
        if resource in self.flasks:
            return self.flasks[resource].remove(item)
        try:
            slot = self._slots.index(item)
        except ValueError:
            return False
        self._slots[slot] = None
        return True

    def item_at(self, slot):
        if not self._valid_slot(slot):
            return None
        return self._slots[slot]

    def slot_of(self, item):
        try:
            return self._slots.index(item)
        except ValueError:
            return None

    def move_item(self, source_slot, target_slot):
        if not self._valid_slot(source_slot) or not self._valid_slot(target_slot):
            return False
        if self._slots[source_slot] is None:
            return False
        if source_slot == target_slot:
            return True
        self._slots[source_slot], self._slots[target_slot] = (
            self._slots[target_slot],
            self._slots[source_slot],
        )
        return True

    def sort_items(self):
        rarity_order = {
            Rarity.LEGENDARY: 0,
            Rarity.EPIC: 1,
            Rarity.RARE: 2,
            Rarity.COMMON: 3,
        }
        type_order = {
            "weapon": 0,
            "armor": 1,
            "potion": 2,
        }
        occupied = self.items
        occupied.sort(key=lambda item: (
            type_order.get(getattr(item, "item_type", None), 99),
            rarity_order.get(getattr(item, "rarity", Rarity.COMMON), 99),
            getattr(item, "display_name", getattr(item, "name", "")).casefold(),
        ))
        self._slots = occupied + [None] * (self.size - len(occupied))

    def _valid_slot(self, slot):
        return type(slot) is int and 0 <= slot < self.size

    def list_items(self): # Возвращает список предметов
        return self.items

    def get_items_by_type(self, item_type):
        return [
            item for item in self.items
            if item.item_type == item_type
        ]

    def get_combat_items(self): # Возвращает список предметов, которые можно юзать в бою
        return [item for item in self.items if getattr(item, "use_in_combat", False)]

    def get_weapons(self): # Возвращает список оружия
        return [item for item in self.items if getattr(item, "is_weapon", False)]


class Item:
    def __init__(
        self,
        name,
        item_type,
        use_in_combat,
        price=1,
        rarity=Rarity.COMMON,
        sell_price=None,
    ):
        self.rarity = rarity
        self.name = name 
        self.item_type = item_type
        self.use_in_combat = use_in_combat
        self.is_weapon = False
        self.price = price
        self.sell_price = sell_price

    def use(self, player):
        return False

class Heal(Item):
    def __init__(self, heal=10, price=1):
        super().__init__(
            "Зелье лечения",
            "potion",
            use_in_combat=True,
            price=price,
        )
        self.heal = heal
    def use(self, player):
        old_health = player.health

        player.health = min(
            player.health + self.heal,
            player.max_health
        )

        if player.health == old_health:
            return False

        return True

class HPFlask(Heal):
    flask_resource = "hp"

    @property
    def restore_amount(self):
        return self.heal


class MPFlask(Item):
    flask_resource = "mp"

    def __init__(self, restore_amount=10, price=1):
        super().__init__("Фласка маны", "potion", use_in_combat=True, price=price)
        self.restore_amount = restore_amount

    def use(self, player):
        return player.restore_mana(self.restore_amount)


class Armor(Item):
    def __init__(self, name, slot, defense, price=1):
        super().__init__(
            name,
            "armor",
            use_in_combat=False,
            price=price,
        )
        self.slot = slot
        self.defense = defense

#class Mana_Heal(Item):
    #def __init__(self, mana_heal=10):
        #super().__init__("Зелье восстановления маны", use_in_combat = True)
        #self.mana_heal = mana_heal
