from item import Inventory
from damage import Damage_type
import random

ARMOR_SLOTS = ("head", "body", "hands", "legs")
CRIT_CHANCE_CAP = 0.30
DODGE_CHANCE_CAP = 0.30

class Player:
    def __init__ (self, name, weapon, character_class=None):
        self.name = name
        self.character_class = None
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0
        self.max_health = 30
        self.health = self.max_health
        self.mana = 10
        self.max_mana = 10
        self.main_hand = None
        self.off_hand = None
        self.head = None
        self.body = None
        self.hands = None
        self.legs = None
        self.inventory = Inventory()
        self.level = 1
        self.exp = 0
        self.exp_to_level = 100
        self.unspent_stat_points = 0
        self.gold = 1
        self.current_location = "village" # Текущая локация
        if character_class is not None:
            self.apply_character_class(character_class)
        if weapon is not None:
            self._put_weapon_in_slots(weapon)

    def apply_character_class(self, character_class):
        self.character_class = character_class
        self.strength = character_class.strength
        self.dexterity = character_class.dexterity
        self.intelligence = character_class.intelligence
        self.max_health = character_class.max_health
        self.health = self.max_health

    def get_physical_damage_bonus(self):
        return self.strength

    def get_direct_damage_bonus(self, damage_type=None):
        if damage_type in (Damage_type.ELEMENTAL, Damage_type.ASTRAL):
            return self.get_magic_damage_bonus()
        if damage_type == Damage_type.PHYSICAL or damage_type is None:
            return self.get_physical_damage_bonus()
        return 0

    def get_crit_bonus(self):
        return self.dexterity * 0.01

    def get_crit_chance(self, weapon_crit_chance=0):
        return min(CRIT_CHANCE_CAP, weapon_crit_chance + self.get_crit_bonus())

    def get_dodge_chance(self):
        return min(DODGE_CHANCE_CAP, self.dexterity * 0.01)

    def get_magic_damage_bonus(self):
        return self.intelligence

    def get_dot_bonus(self):
        return self.intelligence

    def attack(self):
        if self.main_hand:
            damage = random.randint(
                self.main_hand.min_damage,
                self.main_hand.max_damage
            )

            damage += self.get_direct_damage_bonus(
                self.main_hand.damage_type
            )

            crit = random.random() < self.get_crit_chance(
                self.main_hand.crit_chance
            )

            if crit:
                damage *= 2

            return damage, crit

        else:
            return 3, False

    def _is_two_handed(self, weapon):
        return getattr(weapon, "weapon_type", None) == "Двуручное"

    def _is_one_handed(self, weapon):
        return getattr(weapon, "weapon_type", None) == "Одноручное"

    def _put_weapon_in_slots(self, weapon):
        self.main_hand = weapon
        if self._is_two_handed(weapon):
            self.off_hand = weapon
        else:
            self.off_hand = None

    def _clear_weapon_slots(self, weapon):
        self.main_hand = None
        if self.off_hand is weapon:
            self.off_hand = None

    def equip_weapon(self, weapon, slot="main_hand"):
        if not getattr(weapon, "is_weapon", False):
            return False

        if slot == "off_hand":
            return False

        if slot != "main_hand":
            return False

        if not self._is_one_handed(weapon) and not self._is_two_handed(weapon):
            return False

        if weapon not in self.inventory.items:
            return False

        previous = self.main_hand
        self.inventory.remove_item(weapon)

        if previous is not None:
            if not self.inventory.add_item(previous):
                self.inventory.add_item(weapon)
                return False

        self._put_weapon_in_slots(weapon)
        return True

    def unequip_weapon(self, slot="main_hand"):
        if slot == "off_hand":
            return False

        if slot != "main_hand":
            return False

        weapon = self.main_hand
        if weapon is None:
            return False

        if not self.inventory.add_item(weapon):
            return False

        self._clear_weapon_slots(weapon)
        return True

    def get_armor_defense(self):
        total = 0
        for slot in ARMOR_SLOTS:
            armor = getattr(self, slot)
            if armor is not None:
                total += armor.defense
        return total

    def equip_armor(self, armor):
        if getattr(armor, "item_type", None) != "armor":
            return False

        slot = getattr(armor, "slot", None)
        if slot not in ARMOR_SLOTS:
            return False

        if armor not in self.inventory.items:
            return False

        previous = getattr(self, slot)
        self.inventory.remove_item(armor)

        if previous is not None:
            if not self.inventory.add_item(previous):
                self.inventory.add_item(armor)
                return False

        setattr(self, slot, armor)
        return True

    def unequip_armor(self, slot):
        if slot not in ARMOR_SLOTS:
            return False

        armor = getattr(self, slot)
        if armor is None:
            return False

        if not self.inventory.add_item(armor):
            return False

        setattr(self, slot, None)
        return True

    def take_damage(self, damage, damage_type=None): # Получение урона персонажем
        if damage_type is None:
            damage_type = Damage_type.PHYSICAL

        if damage_type == Damage_type.PHYSICAL:
            damage = max(0, damage - self.get_armor_defense())

        self.health -= damage
        if self.health < 0:
            self.health = 0

    def heal(self, amount): # Отхил. Как реализовать?
        self.health = min(self.max_health, self.health + amount)

    def is_alive(self):
        return self.health > 0

    def is_dead(self):
        return self.health <= 0

    def add_exp(self, amount): # Добавляет опыт
        self.exp += amount
        print(f"Получено {amount} опыта. Всего: {self.exp}/{self.exp_to_level}")
        while self.exp >= self.exp_to_level:
            self.level_up()

    def level_up(self): # Повышение уровня
        self.exp -= self.exp_to_level
        self.level += 1

        if self.level <= 10:
            self.exp_to_level = int(self.exp_to_level * 1.25)
        elif self.level <= 20:
            self.exp_to_level = int(self.exp_to_level * 1.15)
        elif self.level <= 30:
            self.exp_to_level = int(self.exp_to_level * 1.09)

        self.max_health = round(30 * (1.1 ** (self.level - 1)))
        self.health = self.max_health
        self.unspent_stat_points += 1

    def allocate_stat(self, stat):
        if self.unspent_stat_points <= 0:
            return False
        if stat not in ("strength", "dexterity", "intelligence"):
            return False
        setattr(self, stat, getattr(self, stat) + 1)
        self.unspent_stat_points -= 1
        return True

    def show_status(self): # Выводит на экран статус игрока
        print(f"\n==={self.name}===")
        print(f"Здоровье: {self.health}/{self.max_health}")
        print(f"Опыт: {self.exp}/{self.exp_to_level}")
        print(f"Уровень: {self.level}")
        print(f"Оружие: {self.main_hand.name if self.main_hand else 'Нет'}")
        print(f"Локация: {self.location}")

    def after_death(self): # Функция для работы с состоянием после смерти
        lost_exp = int(self.exp * 0.2) # Штраф за смерть - потеря 20% опыта
        self.exp -= lost_exp
        self.current_location = "village"
        self.health = self.max_health
        print(f"\nВы погибли. Каким-то чудом Вы проснулись в деревне с головной болью и потерянными {lost_exp} очками опыта")
        input("\nНажмите Enter, чтобы продолжить...")

