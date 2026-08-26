import unittest
from player import Player
from enemy import Enemy, Damage_type
from weapon import Weapon, Rarity
from battle import battle

class TestBattle(unittest.TestCase):
    def test_battle_basic(self):
        player = Player("Hero", Weapon("Sword", 2, 5, 0.1, "Одноручное", Damage_type.PHYSICAL))
        enemy = Enemy("Goblin", 10, level=1, min_damage=1, max_damage=3, crit_chance=0.05, damage_type=Damage_type.PHYSICAL)
        battle(player, enemy)
        self.assertTrue(player.health > 0 or enemy.health <= 0)

if __name__ == "__main__":
    unittest.main()



#"Меч", 3, 7, 0.15, "Одноручное", Damage_type.PHYSICAL
#"Двуручный меч", 8, 15, 0.20, "Двуручное", Damage_type.PHYSICAL
#"Топор", 4, 9, 0.10, "Одноручное", Damage_type.PHYSICAL
#"Двуручный топор", 10, 19, 0.18, "Двуручное", Damage_type.PHYSICAL
#"Кинжал", 1, 5, 0.30, "Одноручное", Damage_type.PHYSICAL
#"Копье", 5, 8, 0.20, "Двуручное", Damage_type.PHYSICAL
#"Дубина", 10, 12, 0.09, "Одноручное", Damage_type.PHYSICAL
#"Двуручная дубина", 17, 19, 0.11, "Двуручное", Damage_type.PHYSICAL

#"Goblin", 15, level=1, min_damage=3, max_damage=3, crit_chance=0.05, damage_type=Damage_type.PHYSICAL
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