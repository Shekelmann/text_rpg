import random
from enemy import Enemy 
from objects import ENEMIES, ENEMY_LOOT 
from battle import battle

#Враги, которые могут встретиться в конкретных локациях
LOCATION_ENEMIES = {
    "forest": ["goblin"],
    "cave": ["skeleton"], 
    "witch's hut": ["rat"],
    "mountain": ["wolf"]
}

def handle_encounter(player, location): # Проверяем, есть ли враги в этой локации 
    if location not in LOCATION_ENEMIES: 
        return

    # Выбираем случайного врага из пула
    enemy_id = random.choice(LOCATION_ENEMIES[location])
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
    enemy.gold = enemy_data["gold"]

    # Запускаем бой
    battle(player, enemy)