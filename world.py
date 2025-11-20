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

	def show_paths(self, current_location): # Возвращает доступные пути {ID локации: описание}
		location = self.location.get(current_location) # Получаем словарь локации по ID
		if location:
			return location["paths"]
		else:
			return {} # Проверка. Если локация существует, возвращаем ее пути. Если не существует, возвращаем пустой словарь

	def move(self, current_location, choice_index): # Перемещает игрока по выбранному номеру пути
		paths = self.show_paths(current_location)
		if not paths:
			return current_location
		keys = list(paths.keys())
		if 0 <= choice_index < len(keys): # Проверка, не является ли индекс отрицательным и не выходит ли за длину списка
			return keys[choice_index] # Игрок выбрал существующее направление
		return current_location # Если игрок ввел число, которое не прошло изначальгую проверку, то он остается в текущей локации