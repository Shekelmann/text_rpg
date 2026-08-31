import unittest
from player import Player 
from enemy import Enemy 
from weapon import Weapon 
from damage import Damage_type

class TestBattle(unittest.TestCase):
    def test_battle_basic(self):
        weapon = Weapon(
            "Меч",
            2,
            5,
            0.1,
            "Одноручное",
            Damage_type.PHYSICAL
        )

        player = Player("Hero", weapon)

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

if __name__ == "main":
    unittest.main()