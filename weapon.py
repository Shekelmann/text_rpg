from enum import Enum
from player import Player
from item import Inventory, Item 

class Weapon(Item):
	def __init__(self, name, min_damage, max_damage, crit_chance, weapon_type, damage_type): # Еще нужно понять, сколько слотов занимает оружие
		
		super().__init__(name, item_type="weapon", use_in_combat = False) # Вызов родительского класса Item
		self.is_weapon = True # Устанавливаем флаг

		self.name = name
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.crit_chance = crit_chance
		self.weapon_type = weapon_type
		self.damage_type = damage_type

	def get_damage(self):
		damage = random.randint(self.min_damage, self.max_damage)
		if random.random() < self.crit_chance:
			return damage * 2, True
		return damage, False

class Rarity(Enum): 
	COMMON = ("Обычный", 1.0, "\033[37m") # Белый
	MAGIC = ("Магический", 1.1, "\033[33m") # Желтый
	RARE = ("Редкий", 1.25, "\033[34m") # Синий
	EPIC = ("Эпический", 1.45, "\033[35m") # Фиолетовый
	LEGENDARY = ("Легендарный", 1.75, "\033[31m") # Красный

	def __init__(self, title, multiplier, color):
		self.title = title
		self.multiplier = multiplier
		self.color = color

	def colored(self, text=None): # Выделяет пуху цветом определенной редкости
		reset = "\033[0m"
		if text:
			return f"{self.color}{text}{reset}"
		return f"{self.color}{self.title}{reset}" # подумать, куда вставить вызов print(Rarity.EPIC.colored())