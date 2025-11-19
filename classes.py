import random
from enum import Enum

class World:
	def __init__(self):
		self.location = {
		"village": {
		"name": 'Деревня "Чёртов луг"', 
		"description": "Обычная маленькая деревня, населенная не очень приветливыми жителями. Всю свою жизнь они не любили чужаков, так как они приносили с собой лишь горе и разрушения. С запада и юга деревня окружена лесами, на востоке раскинулась бескрайняя равнина, которую пересекает большая река. На севере над деревней нависает высокая гора.",
		"paths": {"forest": "в Дремучий лес", "mountain": "к Горе скорби", "plains": "в Поля Хэмвика", "bridge": "к мосту", "tavern": 'в таверну "Три пенька"'}
		}
		#"forest": {"name": "Дремучий лес", "description": "Какой же он дремучий!", "paths":{"village": "Обратно в деревню", "cave": "К подозрительно темной пещере"}},
		#"mountain": {"name": "", "description": "", "paths": {""}},
		#"plains": {"name": "", "description": "", "paths": {""}},
		#"tavern": {"name": "", "description": "", "paths": {""}},
		#"cave": {"name": "", "description": "", "paths": {""}}
		}

	def get_location(self, location_id):
		return self.location.get(location_id)

	def show_paths(self, location_id): # Возвращает доступные связи локаций (пути)
		location = self.get_location(location_id)
		return list(location["paths"].values())

	def can_move(self, from_location, to_location_id): # Проверка возможности перемещения
		location = self.get_location(from_location)
		return to_location_id in location["paths"]

	def move(self, from_location, to_location_id): # Возвращает ID новой локи, в которую пришел герой
		#location = self.get_location(from_location)
		if self.can_move(from_location, to_location_id): 
			return to_location_id
		return None 

class Player:
	def __init__ (self, name, weapon):
		self.name = name
		self.health = 100
		self.max_health = 100
		self.weapon = weapon
		self.inventory =[]
		self.level = 1
		self.exp = 0

	def attack(self): # Базовая атака
		if self.weapon:
			return self.weapon.get_damage()
		else:
			return {"damage": 3, 
			"is_crit": False, 
			"damage_type": "physical"}

	def take_damage(self, damage): # Получение урона персонажем
		self.health -= damage
		if self.health < 0:
			self.health = 0

	def heal(self, amount): # Отхил. Как реализовать?
		self.health = min(self.max_health, self.health + amount)

	def is_alive(self):
		return self.health > 0

	def add_exp(self, amount): # Добавляет опыт
		self.exp = amount
		print(f"Получено {amount} опыта. Всего: {self.exp}/{self.exp_to_level}")
		while self.exp >= self.exp_to_level:
			self.level_up()

	def level_up(self): # Повышение уровня
		self.exp -= self.exp_to_level
		self.level += 1
		self.exp_to_level = int(self,exp_to_level * 1.5)
		self.max_health += 10 * (self.level - 1)
		self.health = self_max_health

	def show_status(self): # Выводит на экран статус игрока
		print(f"\n==={self.name}===")
		print(f"Здоровье: {self.health}/{self.max_health}")
		print(f"Опыт: {self.exp}/{self.exp_to_level}")
		print(f"Уровень: {self.level}")
		print(f"Оружие: {self.weapon.name if self.weapon else 'Нет'}")
		print(f"Локация: {self.location}")

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

class Weapon:
	def __init__(self, name, min_damage, max_damage, crit_chance, damage_type, speed, weapon_type=None): # Еще нужно понять, сколько слотов занимает оружие
		self.name = name
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.crit_chance = crit_chance
		self.weapon_type = weapon_type
		self.damage_type = damage_type
		self.speed = speed

	def get_damage(self):
		damage = random.randint(self.min_damage, self.max_damage)
		if random.random() < self.crit_chance:
			return damage * 2, True
		return damage, False

class Item:
	def __init__(self, name, item_type):
		self.name = name 
		self.item_type = item_type
	#def use_item(self) # Нужно подумать, как использовать предметы. И как переделать этот класс

class Inventory():
    gold = 0
    weapons = []
    loot = []
    potions = []
    scrolls = []
    limit = 100

    def menu_inventory():
    	print ('Золото = ' , inv.golds)
    	print ('Вещи = ' , inv.str_things)
    	print ('Свитки = ' , inv.scrolls)
    	print ('Зелья = ' , inv.potions)
    	print ('Свобдные слоты =' , inv.limit)
    	input("Нажмите Enter для продолжения.")

class Damage_type(Enum):
	PHYSICAL = "Физический урон"
	FIRE = "Огонь"
	ICE = "Лед"
	LIGHTNING = "Молния"
	POISON = "Яд"
	HOLY = "Святой"
	DARK = "Темный"

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
