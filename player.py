from game_io import input, print
from item import Inventory
from damage import (
    Damage_type,
    RESISTIBLE_DAMAGE_TYPES,
    RESISTANCE_CAP,
    reduce_damage_by_resistance,
)
from effects import EffectCollection
from loot import LootFilter
from spell import SpellBook
from flasks import HP_FLASK_RESTORE, MP_FLASK_RESTORE
import math
import random

ARMOR_SLOTS = ("armor",)
ACCESSORY_SLOTS = ("ring_1", "ring_2", "amulet", "belt")
CRIT_CHANCE_CAP = 0.30
DODGE_CHANCE_CAP = 0.30
MIN_PHYSICAL_DAMAGE_RATIO = 0.30
HEALTH_PER_STRENGTH = 5
HEALTH_PER_LEVEL_MULTIPLIER = 1.10

class Player:
    def __init__ (self, name, weapon, character_class=None):
        self.is_player = True
        self.name = name
        self.character_class = None
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0
        self.resistances = {
            damage_type: 0
            for damage_type in RESISTIBLE_DAMAGE_TYPES
        }
        self.effects = EffectCollection()
        self.base_max_health = 120
        self.max_health = self.base_max_health
        self.health = self.max_health
        self.mana = 10
        self.max_mana = 10
        self.main_hand = None
        self.off_hand = None
        self.armor = None
        for slot in ACCESSORY_SLOTS:
            setattr(self, slot, None)
        self.inventory = Inventory()
        self.total_flasks = 6
        self.max_hp_flasks = 3
        self.max_mp_flasks = 3
        self.current_hp_flasks = 3
        self.current_mp_flasks = 3
        self.loot_filter = LootFilter()
        self.spellbook = SpellBook()
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

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.max_health = math.floor(self.max_health)
        self.health = max(0, min(self.max_health, math.floor(self.health)))
        self.__dict__.pop("flasks", None)
        if hasattr(self.inventory, "flasks"):
            del self.inventory.flasks
        self.total_flasks = getattr(self, "total_flasks", 6)
        default_hp = min(3, self.total_flasks)
        self.max_hp_flasks = getattr(self, "max_hp_flasks", default_hp)
        self.max_mp_flasks = getattr(
            self, "max_mp_flasks", self.total_flasks - self.max_hp_flasks
        )
        if (self.max_hp_flasks < 0 or self.max_mp_flasks < 0
                or self.max_hp_flasks + self.max_mp_flasks != self.total_flasks):
            self.max_hp_flasks = default_hp
            self.max_mp_flasks = self.total_flasks - default_hp
        self.current_hp_flasks = min(
            self.max_hp_flasks,
            max(0, getattr(self, "current_hp_flasks", self.max_hp_flasks)),
        )
        self.current_mp_flasks = min(
            self.max_mp_flasks,
            max(0, getattr(self, "current_mp_flasks", self.max_mp_flasks)),
        )
        for slot in ACCESSORY_SLOTS:
            if not hasattr(self, slot):
                setattr(self, slot, None)

    def apply_character_class(self, character_class):
        self.character_class = character_class
        self.strength = character_class.strength
        self.dexterity = character_class.dexterity
        self.intelligence = character_class.intelligence
        from spells import grant_starting_spells
        grant_starting_spells(self, character_class.id)
        self.base_max_health = character_class.max_health
        self.recalculate_max_health()
        self.health = self.max_health

    def learn_spell(self, spell):
        return self.spellbook.learn(spell)

    def add_scroll(self, spell, count=1):
        self.spellbook.add_scroll(spell, count)

    def can_cast_spell(self, spell_id, target=None, *, one_shot=False):
        return not self.spellbook.check(self, spell_id, target, one_shot=one_shot)

    def cast_spell(self, spell_id, target=None, *, one_shot=False):
        return self.spellbook.cast(self, spell_id, target, one_shot=one_shot)

    def calculate_max_health(self):
        level_health = round(
            self.base_max_health
            * (HEALTH_PER_LEVEL_MULTIPLIER ** (self.level - 1))
        )
        return level_health + self.strength * HEALTH_PER_STRENGTH

    def recalculate_max_health(self, restore_to_full=False):
        missing_health = max(0, self.max_health - self.health)
        self.max_health = self.calculate_max_health()
        if restore_to_full:
            self.health = self.max_health
        else:
            self.health = max(0, self.max_health - missing_health)

    def get_physical_damage_bonus(self):
        return self.strength

    def get_direct_damage_bonus(self, damage_type=None):
        if damage_type == Damage_type.ASTRAL:
            return self.get_magic_damage_bonus()
        if damage_type == Damage_type.PHYSICAL or damage_type is None:
            return self.get_physical_damage_bonus()
        return 0

    def get_crit_bonus(self):
        return self.dexterity * 0.01

    def get_crit_chance(self, weapon_crit_chance=0):
        return min(CRIT_CHANCE_CAP, weapon_crit_chance + self.get_crit_bonus())

    def get_dodge_chance(self):
        chance = self.dexterity * 0.01
        for weapon in self.attack_weapons():
            if weapon:
                chance = weapon.get_final_stat("dodge_chance", chance, self)
        return min(DODGE_CHANCE_CAP, max(0, chance))

    def get_magic_damage_bonus(self):
        return self.intelligence

    def get_dot_bonus(self):
        return self.intelligence

    def set_resistance(self, damage_type, resistance):
        if damage_type not in RESISTIBLE_DAMAGE_TYPES:
            return False
        self.resistances[damage_type] = min(
            RESISTANCE_CAP,
            max(0, resistance),
        )
        return True

    def get_resistance(self, damage_type):
        if damage_type not in RESISTIBLE_DAMAGE_TYPES:
            return 0
        return min(
            RESISTANCE_CAP,
            max(0, self.resistances.get(damage_type, 0)),
        )

    def apply_resistance(self, damage, damage_type):
        if damage_type not in RESISTIBLE_DAMAGE_TYPES:
            return damage
        return reduce_damage_by_resistance(
            damage,
            self.get_resistance(damage_type),
        )

    def add_effect(self, effect):
        return self.effects.add(effect)

    def trigger_turn_start_effects(self):
        return self.effects.on_turn_start(self)

    def trigger_action_effects(self, action):
        return self.effects.on_action_performed(self, action)

    def get_attack_damage_range(self, target=None, weapon=None):
        weapon = weapon or self.main_hand
        if weapon is None:
            return (12, 12)
        minimum, maximum = weapon.get_damage_range(self, target)
        bonus = self.get_direct_damage_bonus(weapon.damage_type)
        return (minimum + bonus, maximum + bonus)

    def attack(self, target=None, weapon=None):
        weapon = weapon or self.main_hand
        if weapon:
            damage = random.randint(*self.get_attack_damage_range(target, weapon))

            if weapon.damage_type == Damage_type.PHYSICAL:
                damage = max(0, math.floor(round(weapon.get_final_stat(
                    "attack_physical_damage", damage, self, target
                ), 10)))

            crit = random.random() < self.get_crit_chance(
                weapon.final_crit_chance
            )

            if crit:
                damage *= 2

            return damage, crit

        else:
            return 12, False

    def _is_two_handed(self, weapon):
        return getattr(weapon, "weapon_type", None) == "Двуручное"

    def _is_one_handed(self, weapon):
        return getattr(weapon, "weapon_type", None) == "Одноручное"

    def can_pair_daggers(self, main, off):
        return (getattr(self.character_class, "id", None) == "daredevil"
                and all(self._is_one_handed(item) and getattr(item, "icon_id", None) == "dagger"
                        for item in (main, off)))

    def attack_weapons(self):
        if self.off_hand is not self.main_hand and self.can_pair_daggers(self.main_hand, self.off_hand):
            return (self.main_hand, self.off_hand)
        return (self.main_hand,)

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

    def equip_weapon(self, weapon, slot=None):
        if not getattr(weapon, "is_weapon", False):
            return False

        if slot is None:
            slot = ("off_hand" if self.off_hand is None and self.can_pair_daggers(self.main_hand, weapon)
                    else "main_hand")
        if slot not in ("main_hand", "off_hand"):
            return False

        if not self._is_one_handed(weapon) and not self._is_two_handed(weapon):
            return False

        if self.get_weapon_equip_error(weapon):
            return False

        if weapon not in self.inventory.items:
            return False

        if slot == "off_hand":
            if not self.can_pair_daggers(self.main_hand, weapon):
                return False
            new_main, new_off = self.main_hand, weapon
        else:
            new_main = weapon
            new_off = (weapon if self._is_two_handed(weapon) else
                       self.off_hand if self.can_pair_daggers(weapon, self.off_hand) else None)
        returning = []
        for old in (self.main_hand, self.off_hand):
            if old is not None and old not in (new_main, new_off) and old not in returning:
                returning.append(old)
        free_slots = sum(item is None for item in self.inventory.slots[:self.inventory.size])
        if len(returning) > free_slots + 1:
            return False
        self.inventory.remove_item(weapon)
        for old in returning:
            self.inventory.add_item(old)
        self.main_hand, self.off_hand = new_main, new_off
        return True

    def get_weapon_equip_error(self, weapon):
        required_level = getattr(weapon, "level", 1)
        if required_level > self.level:
            return f"Требуется уровень {required_level}. Ваш уровень: {self.level}."
        return None

    def unequip_weapon(self, slot="main_hand"):
        if slot not in ("main_hand", "off_hand"):
            return False
        if slot == "off_hand" and self.off_hand is self.main_hand:
            return False
        weapon = getattr(self, slot)
        if weapon is None:
            return False

        if not self.inventory.add_item(weapon):
            return False

        if slot == "off_hand":
            self.off_hand = None
        elif self.off_hand is not None and self.off_hand is not weapon:
            # Keep the remaining dagger usable when the main dagger is removed.
            self.main_hand, self.off_hand = self.off_hand, None
        else:
            self._clear_weapon_slots(weapon)
        return True

    def get_armor_defense(self):
        return self.armor.get_defense(self) if self.armor is not None else 0

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

    def unequip_armor(self, slot="armor"):
        if slot not in ARMOR_SLOTS:
            return False

        armor = getattr(self, slot)
        if armor is None:
            return False

        if not self.inventory.add_item(armor):
            return False

        setattr(self, slot, None)
        return True

    def equip_accessory(self, accessory):
        slot = getattr(accessory, "slot", None)
        if (getattr(accessory, "item_type", None) != "accessory"
                or slot not in ACCESSORY_SLOTS
                or accessory not in self.inventory.items):
            return False
        previous = getattr(self, slot, None)
        self.inventory.remove_item(accessory)
        if previous is not None and not self.inventory.add_item(previous):
            self.inventory.add_item(accessory)
            return False
        setattr(self, slot, accessory)
        return True

    def unequip_accessory(self, slot):
        if slot not in ACCESSORY_SLOTS:
            return False
        accessory = getattr(self, slot, None)
        if accessory is None or not self.inventory.add_item(accessory):
            return False
        setattr(self, slot, None)
        return True

    def unequip_item(self, slot):
        if slot in ("main_hand", "off_hand"):
            return self.unequip_weapon(slot)
        if slot in ARMOR_SLOTS:
            return self.unequip_armor(slot)
        if slot in ACCESSORY_SLOTS:
            return self.unequip_accessory(slot)
        return False

    def take_damage(
        self,
        damage,
        damage_type=None,
        bypass_mitigation=False,
    ): # Получение урона персонажем
        old_health = math.floor(self.health)
        self.health = old_health
        if damage_type is None:
            damage_type = Damage_type.PHYSICAL

        if bypass_mitigation:
            calculated_damage = damage
        elif damage_type == Damage_type.PHYSICAL:
            damage = self.effects.modify_incoming_damage(damage, damage_type)
            minimum_damage = math.ceil(damage * MIN_PHYSICAL_DAMAGE_RATIO)
            calculated_damage = max(
                minimum_damage,
                damage - self.get_armor_defense(),
            )
        else:
            calculated_damage = self.apply_resistance(
                self.effects.modify_incoming_damage(damage, damage_type),
                damage_type,
            )

        final_damage = max(0, math.floor(calculated_damage))

        self.health = max(0, self.health - final_damage)
        return old_health - self.health

    def can_use_flask(self, resource):
        if resource not in ("hp", "mp") or not self.is_alive():
            return False
        if self.get_flask_count(resource) <= 0:
            return False
        return (self.health < self.max_health if resource == "hp"
                else self.mana < self.max_mana)

    def use_flask(self, resource):
        if not self.can_use_flask(resource):
            return False
        if resource == "hp":
            self.health = min(self.max_health, self.health + HP_FLASK_RESTORE)
            self.current_hp_flasks -= 1
        else:
            self.restore_mana(MP_FLASK_RESTORE)
            self.current_mp_flasks -= 1
        return True

    def get_flask_count(self, resource):
        if resource == "hp":
            return self.current_hp_flasks
        if resource == "mp":
            return self.current_mp_flasks
        return 0

    def get_max_flask_count(self, resource):
        if resource == "hp":
            return self.max_hp_flasks
        if resource == "mp":
            return self.max_mp_flasks
        return 0

    def set_flask_distribution(self, hp_flasks):
        if type(hp_flasks) is not int or not 0 <= hp_flasks <= self.total_flasks:
            return False
        self.max_hp_flasks = hp_flasks
        self.max_mp_flasks = self.total_flasks - hp_flasks
        self.restore_flasks()
        return True

    def restore_flasks(self):
        self.current_hp_flasks = self.max_hp_flasks
        self.current_mp_flasks = self.max_mp_flasks

    def restore_mana(self, amount):
        before = self.mana
        self.mana = min(self.max_mana, self.mana + amount)
        return self.mana > before

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

        self.recalculate_max_health(restore_to_full=True)
        self.unspent_stat_points += 1

    def allocate_stat(self, stat):
        if self.unspent_stat_points <= 0:
            return False
        if stat not in ("strength", "dexterity", "intelligence"):
            return False
        setattr(self, stat, getattr(self, stat) + 1)
        if stat == "strength":
            self.recalculate_max_health()
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
        input("\nНажмите Enter, чтобы продолжить...", kind="pause")

