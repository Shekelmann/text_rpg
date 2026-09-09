import random


LOCATION_ENEMIES = {
    "forest": ["wolf", "goblin", "likho", "leshy"],
    "cave": ["spider", "mutant", "skeleton", "draugr"],
    "witch's hut": ["goblin", "spirit", "undead"],
    "goblins_camp": ["goblin"],
    "mountain": ["wolf", "orc", "mountain_troll"],
    "old man's hut": ["goblin", "bandit", "orc"],
    "plains": ["orc"],
}

LOCATION_LEVEL_RANGES = {
    "forest": (1, 2),
    "cave": (2, 3),
    "witch's hut": (2, 3),
    "goblins_camp": (3, 4),
    "mountain": (4, 6),
    "old man's hut": (5, 7),
    "plains": (8, 10),
}

RARITY_CHANCES = {
    "common": 0.7,
    "dangerous": 0.3,
    "elite": 0.02,
}

LOCATION_RARITY_CHANCES = {
    "goblins_camp": {
        "common": 0.60,
        "dangerous": 0.25,
        "elite": 0.15,
    },
}


def get_rarity_chances(location_id):
    return LOCATION_RARITY_CHANCES.get(location_id, RARITY_CHANCES)

class World:
    def __init__(self, rng=None):
        self.locations = {
        "village": {
        "name": 'Деревня "Чёртов луг"', 
        "description": "Обычная маленькая деревня, населенная не очень приветливыми жителями. \nВсю свою жизнь они не любили чужаков, так как они приносили с собой лишь горе и разрушение. \nС запада и юга деревня окружена лесами, на востоке раскинулась бескрайняя равнина, которую пересекает большая река. \nНа севере над деревней нависает высокая гора.",
        "paths": {
        "forest": "в Дремучий лес", 
        "mountain": "к Горе скорби", 
        "plains": "в Поля Хэмвика", 
        "tavern": 'в таверну "Три пенька"'}
        },

        "tavern": {
        "name": 'таверна "Три пенька"',
        "description": "Самое популярное место в городе. Выпить, закусить, поспать, повторить",
        "npcs": ["heinrich"],
        "paths": {
        "village": "Обратно в деревню"}
        },

        "forest": {
        "name": "Дремучий лес", 
        "description": "Какой же он дремучий!", 
        "paths": {
        "village": "Обратно в деревню", 
        "cave": "К подозрительно темной пещере",
        "witch's hut": "К ведьминой хижине",
        "goblins_camp": "К лагерю гоблинов"}
        },

        "cave": {
        "name": "Тёмная пещера",
        "description": "В пещере сыро и темно",
        "paths": {
        "forest": "Обратно в лес"}
        },

        "witch's hut": {
        "name": "Ведьмина хижина",
        "description": "Кривая хижина посреди леса. Около нее странно пахнет",
        "paths": {
        "forest": "Обратно в лес"}
        },

        "goblins_camp": {
        "name": "Лагерь гоблинов",
        "description": "Небольшой военный лагерь маленьких жутких существ. Еще они воняют",
        "paths": {
        "forest": "Обратно в лес"}
        },

        "mountain": {
        "name": "Гора скорби", 
        "description": "Высокая гора, окутанная туманом. Издревле жители Чёртового луга ходили к ее подножию, \nчтобы почтить память умерших", 
        "paths": {
        "village": "Обратно в деревню",
        "mine": "В старую заброшенную шахту",
        "old man's hut": "В хижину старца"}
        },

        "mine": {
        "name": "Старая заброшенная шахта", 
        "description": "Некогда в этой шахте добывали железо и полезные минералы. \nС приходом мертвецов рабочие покинули ее", 
        "unavailable_message": "Шахта завалена.",
        "paths": {
        "mountain": "Обратно к Горе скорби"}
        },

        "old man's hut": {
        "name": "Хижина старца", 
        "description": "Отшельник, ушедший от людей 30 лет назад. \nИли 40", 
        "paths": {
        "mountain": "Обратно к Горе скорби",}
        },

        "plains": {
        "name": "Поля Хэмвика", 
        "description": "Пашни, на которых занято треть населения деревни. \nЛюди не рекомендуют идти на дальние поля", 
        "paths": {
        "village": "Обратно в деревню",
        "further_plains": "На дальние поля",
        "orcs_camp": "К лагерю орков"}
        },

        "further_plains": {
        "name": "Дальние поля", 
        "description": "Воздух на этой пашне пропитан смертью и разложением. \nПочему стало так темно?", 
        "paths": {
        "plains": "Обратно на Поля Хэмвика",
        "old_mill": "К старой мельнице",
        "devils_glade": "К Дьявольской поляне",
        "bridge": "На Мост через Брэндистан"}
        },

        "orcs_camp": {
        "name": "Лагерь орков", 
        "description": "Достаточно большой и хорошо укрепленный лагерь зеленокожих мордоворотов. \nИ зачем я сюда сунулся?!", 
        "paths": {
        "plains": "Обратно на Поля Хэмвика"}
        },

        "old_mill": {
        "name": "Старая мельница", 
        "description": "Говорят, дед старины Майдаса построил эту мельницу. \nСейчас она в плачевном состоянии", 
        "paths": {
        "further_plains": "Обратно на Дальние поля"}
        },

        "devils_glade": {
        "name": "Дьявольская поляна", 
        "description": "Место без травы с выложенными в круг камнями. \nВ воздухе пахнет дождем и еще чем-то", 
        "paths": {
        "further_plains": "Обратно на Дальние поля"}
        },

        "bridge": {
        "name": "Мост через Брэндистан", 
        "description": "Типичный мост, который охраняет типичный тролль. \nГде мой клинок?!", 
        "paths": {
        "further_plains": "Обратно на Дальние поля"}
        }
        }
        for location in self.locations.values():
            location["ground_loot"] = []
        self._initialize_combat_states(rng or random)

    def _initialize_combat_states(self, rng):
        for location_id, enemy_pool in LOCATION_ENEMIES.items():
            enemy_count = rng.randint(5, 9)
            level_range = LOCATION_LEVEL_RANGES[location_id]
            rarity_chances = get_rarity_chances(location_id)
            self.locations[location_id]["combat_state"] = {
                "main_encounter_completed": False,
                "optional_enemies": [
                    rng.choice(enemy_pool)
                    for _ in range(enemy_count)
                ],
                "optional_enemy_levels": [
                    rng.randint(*level_range)
                    for _ in range(enemy_count)
                ],
                "optional_enemy_rarities": [
                    rng.choices(
                        list(rarity_chances.keys()),
                        weights=rarity_chances.values(),
                    )[0]
                    for _ in range(enemy_count)
                ],
                "chest_opened": False,
            }

    def get_location_level_range(self, location_id):
        return LOCATION_LEVEL_RANGES.get(location_id)

    def get_unavailable_message(self, location_id):
        location = self.locations.get(location_id)
        if location is None:
            return None
        return location.get("unavailable_message")

    def is_location_available(self, location_id):
        return self.get_unavailable_message(location_id) is None

    def get_combat_state(self, location_id):
        location = self.locations.get(location_id)
        if location is None:
            return None
        return location.get("combat_state")

    def get_location_npc_ids(self, location_id):
        location = self.locations.get(location_id)
        if location is None:
            return ()
        return tuple(location.get("npcs", ()))

    def add_ground_loot(self, location_id, item):
        location = self.locations.get(location_id)
        if location is None:
            return False
        location["ground_loot"].append(item)
        return True

    def get_ground_loot(self, location_id):
        location = self.locations.get(location_id)
        if location is None:
            return ()
        return tuple(location["ground_loot"])

    def take_ground_loot(self, location_id, item):
        location = self.locations.get(location_id)
        if location is None or item not in location["ground_loot"]:
            return False
        location["ground_loot"].remove(item)
        return True

    def complete_main_encounter(self, location_id):
        state = self.get_combat_state(location_id)
        if state is None:
            return False
        state["main_encounter_completed"] = True
        return True

    def get_optional_enemies(self, location_id):
        state = self.get_combat_state(location_id)
        if state is None:
            return ()
        return tuple(state["optional_enemies"])

    def get_optional_enemy_level(self, location_id, enemy_index):
        state = self.get_combat_state(location_id)
        if state is None:
            return None
        levels = state["optional_enemy_levels"]
        if not 0 <= enemy_index < len(levels):
            return None
        return levels[enemy_index]

    def get_optional_enemy_rarity(self, location_id, enemy_index):
        state = self.get_combat_state(location_id)
        if state is None:
            return None
        rarities = state["optional_enemy_rarities"]
        if not 0 <= enemy_index < len(rarities):
            return None
        return rarities[enemy_index]

    def defeat_optional_enemy(self, location_id, enemy_index):
        state = self.get_combat_state(location_id)
        if state is None or not state["main_encounter_completed"]:
            return False
        enemies = state["optional_enemies"]
        if not 0 <= enemy_index < len(enemies):
            return False
        enemies.pop(enemy_index)
        state["optional_enemy_levels"].pop(enemy_index)
        state["optional_enemy_rarities"].pop(enemy_index)
        return True

    def can_hunt_optional_enemies(self, location_id):
        state = self.get_combat_state(location_id)
        return bool(
            state
            and state["main_encounter_completed"]
            and state["optional_enemies"]
        )

    def is_location_cleared(self, location_id):
        state = self.get_combat_state(location_id)
        return bool(
            state
            and state["main_encounter_completed"]
            and not state["optional_enemies"]
        )

    def is_chest_available(self, location_id):
        state = self.get_combat_state(location_id)
        return bool(
            self.is_location_cleared(location_id)
            and not state["chest_opened"]
        )

    def open_chest(self, location_id):
        if not self.is_chest_available(location_id):
            return False
        self.get_combat_state(location_id)["chest_opened"] = True
        return True

    def show_paths(self, current_location): # Возвращает доступные пути {ID локации: описание}
        locations = self.locations.get(current_location) # Получаем словарь локации по ID
        if locations:
            return locations["paths"]
        else:
            return {} # Проверка. Если локация существует, возвращаем ее пути. Если не существует, возвращаем пустой словарь

    def move(self, current_location, choice_index): # Перемещает игрока по выбранному номеру пути
        paths = self.show_paths(current_location)
        if not paths:
            return current_location
        keys = list(paths.keys())
        if 0 <= choice_index < len(keys): # Проверка, не является ли индекс отрицательным и не выходит ли за длину списка
            destination = keys[choice_index]
            if self.is_location_available(destination):
                return destination # Игрок выбрал существующее направление
        return current_location # Если игрок ввел число, которое не прошло изначальгую проверку, то он остается в текущей локации
