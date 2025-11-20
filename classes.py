import random
from enum import Enum

class Enemy:
	def __init__ (self, name, base_health, base_min_damage, base_max_damage, base_crit_chance, damage_type):
		self.name = name
		self.base_health = base_health
		self.base_min_damage = base_min_damage
		self.base_max_damage = base_max_damage
		self.base_crit_chance = base_crit_chance
		self.damage_type = damage_type

		self.level = 1
		self.difficulty = 1
		self.rarity = "common"
		self.health = base_health
		self.min_damage = base_min_damage
		self.max_damage = base_max_damage
		self.crit_chance = base_crit_chance
		self.exp_reward = 0
		self.loot = [] # Лут. Список объектов класса Item

	def scale_with_level(self, level, difficulty=1, rarity="common"): # Повышает хар-ки врага в зависимости от уровня и сложности
		self.level = level
		self.difficulty = difficulty
		self.rarity = rarity

		rarity_multiplier = {"common": (1, "\033[32m"), "dangerous": (1.2, "\033[34m"), "elite": (1.5, "\033[31m")}[rarity] # Уровень редкости врагов. Зеленый, синий, красный

		self.health = int(self.base_health * (1 + 0.2 * (level -1)) * difficulty * rarity_multiplier)
		self.min_damage = int(self.base_min_damage * (1 + 0.15 * (level -1)) * difficulty * rarity_multiplier)
		self.max_damage = int(self.base_max_damage * (1 + 0.15 * (level -1)) * difficulty * rarity_multiplier)
		self.crit_chance = min(0.5, self.base_crit_chance + 0.02 * (level - 1))

		self.exp_reward = level * 10 * difficulty * rarity_multiplier # Награда за победу над врагом в виде опыта



	def attack(self): # Базовая атака
		return random.randint(self.min_damage, self.max_damage)

	def take_damage(self, amount): # Получение урона врагом
		self.health -= amount

	def is_alive(self):
		return self.health > 0

class Enemy_Rarity(Enum): 
	COMMON = ("Обычный", 1.0, "\033[32m") 
	DANGEROUS = ("Опасный", 1.25, "\033[34m") # Синий
	ELITE = ("Элитный", 1.75, "\033[31m") # Красный

class Damage_type(Enum):
	PHYSICAL = "Физический урон"
	FIRE = "Огонь"
	ICE = "Лед"
	LIGHTNING = "Молния"
	POISON = "Яд"
	HOLY = "Святой"
	DARK = "Темный"


