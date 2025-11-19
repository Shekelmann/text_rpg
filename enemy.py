import random

class Enemy:
	def __init__ (self, name="Гоблин", hp=30, min_damage=2, max_damage=6):
		self.name = name
		self.hp = hp
		self.min_damage = min_damage
		self.max_damage = max_damage

	def attack(self):
		return random.randint(self.min_damage, self.max_damage)

	def take_damage(self, amount):
		self.hp -= amount

	def is_alive(self):
		return self.hp > 0