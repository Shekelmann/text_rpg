from classes import Enemy, Item, Damage_type
from player import Player, Inventory
from world import World
from weapon import Weapon, Rarity

# Оружие
# базовое оружие
sword = Weapon("Меч", 3, 7, 0.15, "Одноручное", Damage_type.PHYSICAL, 1)
sword_2h = Weapon("Двуручный меч", 8, 15, 0.20, "Двуручное", Damage_type.PHYSICAL, 0.5)
axe = Weapon("Топор", 4, 9, 0.10, "Одноручное", Damage_type.PHYSICAL, 1)
axe_2h = Weapon("Двуручный топор", 10, 19, 0.18, "Двуручное", Damage_type.PHYSICAL, 0.5)
dagger = Weapon("Кинжал", 1, 5, 0.30, "Одноручное", Damage_type.PHYSICAL, 1.5)
spear = Weapon("Копье", 5, 8, 0.20, "Двуручное", Damage_type.PHYSICAL, 0.8)
club = Weapon("Дубина", 10, 12, 0.09, "Одноручное", Damage_type.PHYSICAL, 0.8)
club_2h = Weapon("Двуручная дубина", 17, 19, 0.11, "Двуручное", Damage_type.PHYSICAL, 0.4)

# магическое оружие

#light_totem = Weapon("Тотем молнии", 10, 17, 0.05, "Одноручное", Damage_type.LIGHTNING, 1,5) # Подумать, как прикрутить ману

# легендарное оружие  



# Враги
# враги начала игры
goblin_lvl_1 = Enemy("Гоблин", 15, 1, 1, 6, 0.10, 1, 1)
rat_lvl_1 = Enemy("Крыса", 5, 1, 1, 3, 0.01, 1, 0.5)
spider_lvl_1 = Enemy("Паук", 7, 1, 2, 5, 0.15, 1, 0.7)
skeleton_lvl_1 = Enemy("Скелет", 20, 1, 3, 9, 0.15, 0.5, 1.5)

#goblin_lvl_2 = Enemy("Гоблин", 15, 1, 1, 6, 0.10, 1, 1) # Поднять характеристики
#rat_lvl_2 = Enemy("Крыса", 5, 1, 1, 3, 0.01, 1,5, 0.5)
#spider_lvl_2 = Enemy("Паук", 7, 1, 2, 5, 0.15, 1, 5, 0.7)
#skeleton_lvl_2 = Enemy("Скелет", 20, 1, 3, 9, 0.15, 0.5, 1.5)

#goblin_lvl_3 = Enemy("Гоблин", 15, 1, 1, 6, 0.10, 1, 1)
#rat_lvl_3 = Enemy("Крыса", 5, 1, 1, 3, 0.01, 1,5, 0.5)
#spider_lvl_3 = Enemy("Паук", 7, 1, 2, 5, 0.15, 1, 5, 0.7)
#skeleton_lvl_3 = Enemy("Скелет", 20, 1, 3, 9, 0.15, 0.5, 1.5)

#goblin_lvl_4 = Enemy("Гоблин", 15, 1, 1, 6, 0.10, 1, 1)
#rat_lvl_4 = Enemy("Крыса", 5, 1, 1, 3, 0.01, 1,5, 0.5)
#spider_lvl_4 = Enemy("Паук", 7, 1, 2, 5, 0.15, 1, 5, 0.7)
#skeleton_lvl_4 = Enemy("Скелет", 20, 1, 3, 9, 0.15, 0.5, 1.5)

# враги середины игры
#hellhound = Enemy("Адская гончая", 18, 5, 7, 9, 0.2, 1, 5, 3)
#brigand = Enemy("Бандит", 30, 5, 7, 12, 0.2, 1, 3)
#zombie = Enemy("Мертвец", 35, 5, 3, 7, 0.1, 0,5, 2)
#orc = Enemy("Орк", 40, 5, 5, 14, 0.2, 1, 4)

# Айтимы
#heal = Item("Лекарство", "Зелье")
#mana = Item("Источник маны", "Зелье")