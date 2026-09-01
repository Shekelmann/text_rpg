#from weapon import Weapon

class Inventory:
    def __init__ (self, size = 20):
        self.size = size # Макс кол-во предметов
        self.items = [] # Список предметов

    def is_full(self):
        return len(self.items) >= self.size

    def add_item(self, item): # Добавление предмета и проверка на заполненность инвентаря
        if self.is_full():
            return False
        self.items.append(item)
        return True

    def remove_item(self, item): # Удаление предмета из инвентаря
        if item in self.items:
            self.items.remove(item)
            return True
        return False

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
    def __init__(self, name, item_type, use_in_combat):
        self.name = name 
        self.item_type = item_type
        self.use_in_combat = use_in_combat
        self.is_weapon = False

    def use(self, player):
        return False

class Heal(Item):
    def __init__(self, heal=10):
        super().__init__(
            "Зелье лечения",
            "potion",
            use_in_combat = True
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

class Armor(Item):
    def __init__(self, name, slot, defense):
        super().__init__(
            name,
            "armor",
            use_in_combat=False
        )
        self.slot = slot
        self.defense = defense

#class Mana_Heal(Item):
    #def __init__(self, mana_heal=10):
        #super().__init__("Зелье восстановления маны", use_in_combat = True)
        #self.mana_heal = mana_heal