import random
from classes import Enemy, Damage_type
from player import Player
from item import Inventory, Item 
from world import World
from weapon import Weapon, Rarity

# Оружие
# базовое оружие
WEAPONS = {
"sword": Weapon("Меч", 3, 7, 0.15, "Одноручное", Damage_type.PHYSICAL),
"sword_2h": Weapon("Двуручный меч", 8, 15, 0.20, "Двуручное", Damage_type.PHYSICAL),
"axe": Weapon("Топор", 4, 9, 0.10, "Одноручное", Damage_type.PHYSICAL),
"axe_2h": Weapon("Двуручный топор", 10, 19, 0.18, "Двуручное", Damage_type.PHYSICAL),
"dagger": Weapon("Кинжал", 1, 5, 0.30, "Одноручное", Damage_type.PHYSICAL),
"spear": Weapon("Копье", 5, 8, 0.20, "Двуручное", Damage_type.PHYSICAL),
"club": Weapon("Дубина", 10, 12, 0.09, "Одноручное", Damage_type.PHYSICAL),
"club_2h": Weapon("Двуручная дубина", 17, 19, 0.11, "Двуручное", Damage_type.PHYSICAL)
}

# магическое оружие

#light_totem = Weapon("Тотем молнии", 10, 17, 0.05, "Одноручное", Damage_type.LIGHTNING, 1,5) # Подумать, как прикрутить ману

# легендарное оружие  



# Враги
ENEMIES = {
"goblin": Enemy("Гоблин", 15, 1, 6, 0.10, Damage_type.PHYSICAL),
"rat": Enemy("Крыса", 5, 1, 3, 0.01, Damage_type.PHYSICAL),
"spider": Enemy("Паук", 7, 2, 5, 0.15, Damage_type.PHYSICAL),
"skeleton": Enemy("Скелет", 20, 3, 9, 0.15, Damage_type.PHYSICAL)
}

# враги середины игры
#hellhound = Enemy("Адская гончая", 18, 5, 7, 9, 0.2, 1, 5, 3)
#brigand = Enemy("Бандит", 30, 5, 7, 12, 0.2, 1, 3)
#zombie = Enemy("Мертвец", 35, 5, 3, 7, 0.1, 0,5, 2)
#orc = Enemy("Орк", 40, 5, 5, 14, 0.2, 1, 4)

# Айтимы
#heal = Item("Лекарство", "Зелье")
#mana = Item("Источник маны", "Зелье")

# Таблица лута
FOREST_LOOT = {
	"имя предмета": "шанс выпадения, цифры без скобок"
}