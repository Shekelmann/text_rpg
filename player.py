from weapons import Weapon

class Player:
	def __init__ (self, name, hp=50, weapon=None):
		self.name = name
		self.hp = hp
		self.weapon = weapon or Weapon('Кулаки', 1, 3)

	def attack(self):
		return self.weapon.get_damage()

	def take_damage(self, amount):
		self.hp -= amount

	def is_alive(self):
		return self.hp > 0