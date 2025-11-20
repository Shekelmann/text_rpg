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
"goblin": {
"name": "Гоблин", 
"health": 15, 
"min_damage": 3, 
"max_damage": 7, 
"crit_chance": 0.10, 
"damage_type": Damage_type.PHYSICAL
},

"rat": {
"name": "Крыса", 
"health": 5, 
"min_damage": 1, 
"max_damage": 3, 
"crit_chance": 0.01, 
"damage_type": Damage_type.PHYSICAL
},

"spider": {
"name": "Паук", 
"health": 7, 
"min_damage": 2, 
"max_damage": 5, 
"crit_chance": 0.20, 
"damage_type": Damage_type.PHYSICAL
},

"skeleton": {
"name": "Скелет", 
"health": 20, 
"min_damage": 4, 
"max_damage": 9, 
"crit_chance": 0.15, 
"damage_type": Damage_type.PHYSICAL
}
}


ITEMS = {
	"heal": Item("Зелье лечения", "potion", use_in_combat=True)
}


# враги середины игры
#hellhound = "Адская гончая"
#brigand = "Бандит"
#zombie = "Мертвец"
#orc = "Орк"


# Таблица лута
FOREST_LOOT = {
	"heal": 0.5
}