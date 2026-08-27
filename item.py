#from weapon import Weapon

class Inventory:
    def __init__ (self, size = 20):
        self.size = size # Макс кол-во предметов
        self.items = [] # Список предметов

    def is_full(self):
        return len(self.items) >= self.size

    def add_item(self, item): # Добавление предмета и проверка на заполненность инвентаря
        if self.is_full():
            print(f"Инвентарь заполнен. (макс. {self.size})")
            return False
        self.items.append(item)
        print(f"Вы получили: {item.name}")
        return True

    def show_inventory(self):
        print("\n=== Инвентарь ===")

        if not self.items:
            print("Инвентарь пуст.")
            return

        for i, item in enumerate(self.items, 1):
            print(f"{i}. {item.name}")

    def remove_item(self, item): # Удаление предмета из инвентаря
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def list_items(self): # Возвращает список предметов
        return self.items

    def get_combat_items(self): # Возвращает список предметов, которые можно юзать в бою
        return [item for item in self.items if getattr(item, "use_in_combat", False)]

    def get_weapons(self): # Возвращает список оружия
        return [item for item in self.items if getattr(item, "is_weapon", False)]

        #использование зелий
    def use_potion(player):
        print("\n=== Зелья ===")

        potions = []

        for item in player.inventory.items:
            if item.item_type == "potion":
                potions.append(item)

        if not potions:
            print("У вас нет зелий.")
            return

        for i, potion in enumerate(potions, 1):
            print(f"{i}. {potion.name}")

        print("0. Назад")

        choice = input("Выберите зелье: ")

        if choice == "0":
            return

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(potions):
                potion = potions[index]

                if potion.name == "Зелье лечения":
                    player.health = min(
                        player.health + 30,
                        player.max_health
                    )

                    player.inventory.items.remove(potion)

                    print(f"Вы использовали {potion.name}.")
                    print(f"HP: {player.health} / {player.max_health}")


class Item:
    def __init__(self, name, item_type, use_in_combat):
        self.name = name 
        self.item_type = item_type
        self.use_in_combat = use_in_combat
        self.is_weapon = False

    def use(self, player):
        print(f"{self.name} нельзя использовать")

class Heal(Item):
    def __init__(self, heal=10):
        super().__init__("Зелье лечения", use_in_combat = True)
        self.heal = heal

#class Mana_Heal(Item):
    #def __init__(self, mana_heal=10):
        #super().__init__("Зелье восстановления маны", use_in_combat = True)
        #self.mana_heal = mana_heal