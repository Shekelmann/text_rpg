from player import Player, Weapon

def test_player_creation():
    """Тест создания игрока"""
    player = Player("Тестовый герой")
    
    # Проверяем начальные значения
    assert player.name == "Тестовый герой"
    assert player.health == 100
    assert player.weapon is None
    assert player.location == "village"
    print("✅ Тест создания игрока пройден")

def test_player_attack():
    """Тест атаки игрока"""
    player = Player("Боец")
    player.weapon = Weapon("Меч", 5, 10)
    
    # Тестируем атаку
    damage_info = player.attack()
    print(damage_info)
    
    # Проверяем что урон в допустимом диапазоне
    assert 5 <= damage_info["damage"] <= 20  # 5-10 или 10-20 если крит
    assert isinstance(damage_info["is_crit"], bool)
    print("✅ Тест атаки игрока пройден")

def test_player_damage():
    """Тест получения урона"""
    player = Player("Цель")
    initial_health = player.health
    
    player.take_damage(30)
    
    assert player.health == initial_health - 30
    assert player.is_alive() == True
    print("✅ Тест получения урона пройден")

def test_player_death():
    """Тест смерти игрока"""
    player = Player("Смертник")
    player.take_damage(150)  # Больше чем максимальное здоровье
    
    assert player.health == 0
    assert player.is_alive() == False
    print("✅ Тест смерти игрока пройден")

# Запуск всех тестов
if __name__ == "__main__":
    test_player_creation()
    test_player_attack() 
    test_player_damage()
    test_player_death()
    print("🎉 Все тесты Player пройдены!")