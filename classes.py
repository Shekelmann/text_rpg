import random
from enum import Enum

class Enemy:
	def __init__ (self, name, health, level, min_damage, max_damage, crit_chance, speed, difficulty):
		self.name = name
		self.health = health
		self.level = level
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.speed = speed
		self.difficulty = difficulty
		self.exp_reward = level * 10 * difficulty

	def attack(self): # Базовая атака
		return random.randint(self.min_damage, self.max_damage)

	def take_damage(self, amount): # Получение урона врагом
		self.health -= amount

	def is_alive(self):
		return self.health > 0

class Item:
	def __init__(self, name, item_type):
		self.name = name 
		self.item_type = item_type
	#def use_item(self) # Нужно подумать, как использовать предметы. И как переделать этот класс

class Damage_type(Enum):
	PHYSICAL = "Физический урон"
	FIRE = "Огонь"
	ICE = "Лед"
	LIGHTNING = "Молния"
	POISON = "Яд"
	HOLY = "Святой"
	DARK = "Темный"


