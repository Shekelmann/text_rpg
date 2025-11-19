import random

class Weapon:
	def __init__(self, name, min_damage, max_damage, crit_chance=0.1):
		self.name = name
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.crit_chance = crit_chance

	def get_damage(self):
		damage = random.randint(self.min_damage, self.max_damage)
		if random.random() < self.crit_chance:
			return damage * 2, True
		return damage, False