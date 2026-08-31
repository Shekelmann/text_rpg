import random
from enemy import Enemy 
from objects import ENEMIES, ENEMY_LOOT 
from battle import battle

#Враги, которые могут встретиться в конкретных локациях
LOCATION_ENEMIES = {
    
    "forest": {
        "common": ["goblin", "wolf", "rat"],
        "dangerous": ["goblin", "wolf"]
    },
    
    "cave": {
        "common": ["goblin", "spider", "skeleton"],
        "dangerous": ["goblin", "skeleton"],
        "elite": ["skeleton"]
    }
}

def handle_encounter(player, location): # Проверяем, есть ли враги в этой локации 
    if location not in LOCATION_ENEMIES: 
        return

    #Выбираем редкость врага
    rarity = random.choices( 
        list(RARITY_CHANCES.keys()),
        weights=RARITY_CHANCES.values() 
    )[0]

    #Выбираем врага из пула выбранной редкости
    enemy_id = random.choice(
        LOCATION_ENEMIES[location][rarity]
    )

    enemy_data = ENEMIES[enemy_id]

    # Создаём экземпляр врага
    enemy = Enemy(
        enemy_data["name"],
        enemy_data["health"],
        enemy_data["min_damage"],
        enemy_data["max_damage"],
        enemy_data["crit_chance"],
        enemy_data["damage_type"],
    )
    enemy.loot = ENEMY_LOOT.get(enemy_id, {})
    enemy.gold = enemy_data.get("gold", (0, 0))
    enemy.scale_with_level(
        player.level,
        rarity=rarity
    )

    # Запускаем бой
    battle(player, enemy)

RARITY_CHANCES = {
    "common": 0.7,
    "dangerous": 0.3,
    "elite": 0.02
}