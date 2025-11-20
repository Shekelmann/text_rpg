class Player:
	def __init__ (self, name, weapon):
		self.name = name
		self.health = 100
		self.max_health = 100
		self.weapon = weapon
		self.inventory =[]
		self.level = 1
		self.exp = 0
		self.current_location = "village" # Текущая локация

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

	def is_dead(self):
		return self.health <= 0

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

	def after_death(self): # Функция для работы с состоянием после смерти
		lost_exp = int(self.exp * 0.2) # Штраф за смерть - потеря 20% опыта
		self.exp -= lost_exp
		self.current_location = "village"
		print(f"\nВы погибли. Каким-то чудом Вы проснулись в деревне с головной болью и потерянными {lost_exp} очками опыта")

