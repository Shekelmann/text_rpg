#from main import current_location

class World:
	def __init__(self):
		self.location = {
		"village": {
		"name": 'Деревня "Чёртов луг"', 
		"description": "Обычная маленькая деревня, населенная не очень приветливыми жителями. \nВсю свою жизнь они не любили чужаков, так как они приносили с собой лишь горе и разрушение. \nС запада и юга деревня окружена лесами, на востоке раскинулась бескрайняя равнина, которую пересекает большая река. \nНа севере над деревней нависает высокая гора.",
		"paths": {
		"forest": "в Дремучий лес", 
		"mountain": "к Горе скорби", 
		"plains": "в Поля Хэмвика", 
		#"bridge": "к мосту", 
		"tavern": 'в таверну "Три пенька"'}
		},

		"forest": {
		"name": "Дремучий лес", 
		"description": "Какой же он дремучий!", 
		"paths": {
		"village": "Обратно в деревню", 
		"cave": "К подозрительно темной пещере",
		"witch's hut": "К ведьминой хижине"}
		},

		"mountain": {
		"name": "Гора скорби", 
		"description": "Высокая гора, окутанная туманом. Издревле жители Чёртового луга ходили к ее подножию, \nчтобы почтить память умерших", 
		"paths": {
		"village": "Обратно в деревню",
		"mine": "В старую заброшенную шахту",
		"old man's hut": "В хижину старца"}
		}

		#"plains": {"name": "", "description": "", "paths": {""}},
		#"tavern": {"name": "", "description": "", "paths": {""}},
		#"cave": {"name": "", "description": "", "paths": {""}},
		#"bridge": {"name": "", "description": "", "paths": {""}}
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