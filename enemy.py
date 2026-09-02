import random
from damage import Damage_type
from enum import Enum
import math
from loot import LootTable

class Enemy:
    def __init__ (self, name, base_health, base_min_damage, base_max_damage, base_crit_chance, damage_type):
        self.name = name
        self.base_health = base_health
        self.base_min_damage = base_min_damage
        self.base_max_damage = base_max_damage
        self.base_crit_chance = base_crit_chance
        self.damage_type = damage_type
        self.physical_resistance = 0
        self.elemental_resistance = 0
        self.astral_resistance = 0
        self.level = 1
        self.difficulty = 1
        self.rarity = "common"
        self.health = base_health
        self.max_health = base_health
        self.min_damage = base_min_damage
        self.max_damage = base_max_damage
        self.crit_chance = base_crit_chance
        self.exp_reward = base_health #пока привяжем к здоровью, потом level * 10 * difficulty * rarity
        self.loot = LootTable()
        self.gold = (0, 0)

    def scale_with_level(self, level, difficulty=1, rarity="common"):
        rarity_multiplier = { 
        "common": Enemy_Rarity.COMMON.value[1], 
        "dangerous": Enemy_Rarity.DANGEROUS.value[1], 
        "elite": Enemy_Rarity.ELITE.value[1] 
        }[rarity]

        self.level = level
        self.difficulty = difficulty
        self.rarity = rarity

        level_health_multiplier = 1 + 0.2 * (level - 1)
        level_damage_multiplier = 1 + 0.15 * (level - 1)

        self.max_health = math.ceil(
            self.base_health
            * level_health_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.health = self.max_health

        self.min_damage = math.ceil(
            self.base_min_damage
            * level_damage_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.max_damage = math.ceil(
            self.base_max_damage
            * level_damage_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.crit_chance = min(
            0.5,
            self.base_crit_chance + 0.02 * (level - 1)
        )

        self.exp_reward = math.ceil(
            level
            * 10
            * difficulty
            * rarity_multiplier
        )



    def attack(self): # Базовая атака
        return random.randint(self.min_damage, self.max_damage)

    def take_damage(self, amount, damage_type=None): # Получение урона врагом
        if damage_type == Damage_type.PHYSICAL:
            resistance = self.physical_resistance
        elif damage_type == Damage_type.ELEMENTAL:
            resistance = self.elemental_resistance
        elif damage_type == Damage_type.ASTRAL:
            resistance = self.astral_resistance
        else:
            resistance = 0
        
        damage = max(0, amount - resistance) 
        self.health -= damage

    def is_alive(self):
        return self.health > 0

class Enemy_Rarity(Enum): 
    COMMON = ("Обычный", 1.0, "\033[32m") 
    DANGEROUS = ("Опасный", 1.25, "\033[34m") # Синий
    ELITE = ("Элитный", 1.75, "\035[31m") # Фиолетовый
