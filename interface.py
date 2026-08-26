#def show_player_status(player):
    #WIDTH = 36

    #def box_line(text):
        #print("║ " + text.ljust(WIDTH - 4) + " ║")

    #print("╔" + "═" * (WIDTH - 2) + "╗")

    #box_line(f"{player.name:<26}")
    #box_line(f"Класс: {'—':<20}")
    #box_line(f"HP:      {player.health:<3} / {player.max_health:<3}")
    #box_line(f"Мана:    {player.mana:<3} / {player.max_mana:<3}")
    #box_line(f"Стамина: {player.stamina:<3} / {player.max_stamina:<3}")
    #box_line(f"Золото:  {player.gold:<18}")
    #box_line(f"Опыт:    {player.exp:<18}")

    #print("╚" + "═" * (WIDTH - 2) + "╝")

def show_box(lines):
    WIDTH = 36

    print("╔" + "═" * (WIDTH - 2) + "╗")

    for line in lines:
        print("║ " + line.ljust(WIDTH - 4) + " ║")

    print("╚" + "═" * (WIDTH - 2) + "╝")

def show_player_status(player):
    show_box([
        player.name,
        "Класс: —",
        f"HP: {player.health} / {player.max_health}",
        f"Мана: {player.mana} / {player.max_mana}",
        #f"Стамина: {player.stamina} / {player.max_stamina}",
        f"Золото: {player.gold}",
        f"Опыт: {player.exp}"
    ])

def show_enemy_status(enemy):
    show_box([
        enemy.name,
        f"HP: {enemy.health} / {enemy.max_health}"
    ])