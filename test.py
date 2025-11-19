from classes import World

def test_world_creation():
    """Тест создания мира"""
    world = World()
    
    # Проверяем что локации загрузились
    assert "village" in world.locations
    assert "forest" in world.locations
    print("✅ Тест создания мира пройден")

def test_location_access():
    """Тест доступа к локациям"""
    world = World()
    
    location = world.get_location("village")
    
    assert location["name"] == 'Деревня "Чёртов луг"'
    assert "description" in location
    assert "paths" in location
    print("✅ Тест доступа к локациям пройден")

def test_movement():
    """Тест перемещения между локациями"""
    world = World()
    
    # Проверяем можно ли пойти из старта в лес
    can_move = world.can_move_to("village", "forest")
    assert can_move == True
    
    # Проверяем что нельзя пойти в несуществующую локацию
    can_move_invalid = world.can_move_to("village", "non_existent")
    assert can_move_invalid == False
    print("✅ Тест перемещения пройден")

def test_paths():
    """Тест выходов из локаций"""
    world = World()
    
    exits = world.get_available_exits("village")
    
    # Проверяем что есть ожидаемые выходы
    assert "forest" in paths or "в лес" in str(paths)
    print("✅ Тест выходов пройден")

# Запуск тестов
if name == "__main__":
    test_world_creation()
    test_location_access()
    test_movement()
    test_paths()
    print("🎉 Все тесты World пройдены!")