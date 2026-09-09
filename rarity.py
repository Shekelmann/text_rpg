from enum import Enum

class Rarity(Enum): 
    COMMON = ("Обычный", 1.0, "\033[37m") # Белый
    RARE = ("Редкий", 1.25, "\033[34m") # Синий
    EPIC = ("Эпический", 1.45, "\033[35m") # Фиолетовый
    LEGENDARY = ("Легендарный", 1.75, "\033[31m") # Красный

    def __init__(self, title, multiplier, color):
        self.title = title
        self.multiplier = multiplier
        self.color = color

    def colored(self, text=None): # Выделяет пуху цветом определенной редкости
        reset = "\033[0m"
        if text:
            return f"{self.color}{text}{reset}"
        return f"{self.color}{self.title}{reset}" # подумать, куда вставить вызов print(Rarity.EPIC.colored())
