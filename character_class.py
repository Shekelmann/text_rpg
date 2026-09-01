class CharacterClass:
    def __init__(
        self,
        class_id,
        name,
        description,
        max_health,
        strength,
        dexterity,
        intelligence,
        features=None,
    ):
        self.id = class_id
        self.name = name
        self.description = description
        self.max_health = max_health
        self.strength = strength
        self.dexterity = dexterity
        self.intelligence = intelligence
        self.features = features if features is not None else {}


CLASS_LIST = [
    CharacterClass(
        "bruiser",
        "Бугай",
        "Выносливый боец ближнего боя. Полагается на здоровье и силу.",
        max_health=30,
        strength=4,
        dexterity=1,
        intelligence=1,
    ),
    CharacterClass(
        "daredevil",
        "Лихач",
        "Быстрый и точный воин. Делает ставку на ловкость и критические удары.",
        max_health=25,
        strength=2,
        dexterity=3,
        intelligence=1,
    ),
    CharacterClass(
        "herald",
        "Глашатай",
        "Слабее телом, сильнее разумом. Интеллект усиливает магию и длительный урон.",
        max_health=20,
        strength=1,
        dexterity=2,
        intelligence=3,
    ),
]

CLASSES = {character_class.id: character_class for character_class in CLASS_LIST}
