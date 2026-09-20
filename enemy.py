import random
from damage import Damage_type
from enum import Enum
import math
from loot import LootTable
from effects import EffectCollection
from intent import EnemyIntent

class Enemy:
    def __init__ (
        self, name, base_health, base_min_damage, base_max_damage,
        base_crit_chance, damage_type, dodge_chance=0, armor=0,
        exp_reward=None, damage_types=None, damage_type_effects=None,
    ):
        if not 0 <= dodge_chance <= 1:
            raise ValueError("Dodge chance must be between 0 and 1")
        if type(armor) is not int or armor < 0:
            raise ValueError("Armor must be a nonnegative integer")
        self.name = name
        self.base_health = base_health
        self.base_min_damage = base_min_damage
        self.base_max_damage = base_max_damage
        self.base_crit_chance = base_crit_chance
        self.damage_type = damage_type
        capabilities = tuple(damage_types or (damage_type,))
        self.damage_types = tuple(dict.fromkeys((damage_type, *capabilities)))
        self.damage_type_effects = {
            key: tuple(value)
            for key, value in (damage_type_effects or {}).items()
        }
        self.dodge_chance = dodge_chance
        self.armor = armor
        self.level = 1
        self.difficulty = 1
        self.rarity = "common"
        self.health = base_health
        self.max_health = base_health
        self.min_damage = base_min_damage
        self.max_damage = base_max_damage
        self.crit_chance = base_crit_chance
        self.base_exp_reward = base_health if exp_reward is None else exp_reward
        self.exp_reward = self.base_exp_reward
        self.loot = LootTable()
        self.gold = (0, 0)
        self.effects = EffectCollection()
        self.intent = self.choose_next_intent()

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.damage_types = tuple(getattr(
            self, "damage_types", (self.damage_type,)
        ))
        if self.damage_type not in self.damage_types:
            self.damage_types = (self.damage_type, *self.damage_types)
        self.damage_type_effects = dict(getattr(
            self, "damage_type_effects", {}
        ))
        if not hasattr(self, "base_exp_reward"):
            self.base_exp_reward = getattr(self, "exp_reward", self.base_health)
        try:
            self.intent = EnemyIntent(self.intent)
            if self.intent not in self.get_available_intents():
                self.prepare_next_intent()
        except (AttributeError, TypeError, ValueError):
            self.prepare_next_intent()

    def get_available_intents(self):
        """Extension point for future enemy action pools and archetypes."""
        if self.damage_type == Damage_type.ASTRAL:
            return (EnemyIntent.ASTRAL_ATTACK,)
        return (EnemyIntent.PHYSICAL_ATTACK,)

    def choose_next_intent(self):
        return self.get_available_intents()[0]

    def prepare_next_intent(self):
        self.intent = self.choose_next_intent()
        return self.intent

    def scale_with_level(self, level, difficulty=1, rarity="common"):
        rarity_multiplier = { 
        "common": Enemy_Rarity.COMMON.value[1], 
        "dangerous": Enemy_Rarity.DANGEROUS.value[1], 
        "elite": Enemy_Rarity.ELITE.value[1] 
        }[rarity]

        self.level = level
        self.difficulty = difficulty
        self.rarity = rarity

        level_health_multiplier = 1 + 0.12 * (level - 1)
        level_damage_multiplier = 1 + 0.08 * (level - 1)

        self.max_health = math.ceil(
            self.base_health
            * level_health_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.health = self.max_health

        self.min_damage = math.ceil(
            self.base_min_damage
            * level_damage_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.max_damage = math.ceil(
            self.base_max_damage
            * level_damage_multiplier
            * difficulty
            * rarity_multiplier
        )

        self.crit_chance = min(
            0.5,
            self.base_crit_chance + 0.02 * (level - 1)
        )

        self.exp_reward = math.ceil(
            self.base_exp_reward
            * level
            * difficulty
            * rarity_multiplier
        )



    def attack(self): # Базовая атака
        damage = random.randint(self.min_damage, self.max_damage)
        critical = random.random() < self.crit_chance
        return (damage * 2 if critical else damage), critical

    def get_dodge_chance(self):
        return min(1, max(0, self.dodge_chance))

    def get_armor_defense(self):
        return max(0, math.floor(self.effects.modify_armor(self.armor)))

    def take_damage(
        self,
        amount,
        damage_type=None,
        bypass_mitigation=False,
        armor_penetration=0,
    ): # Получение урона врагом
        old_health = self.health
        if damage_type is None:
            damage_type = Damage_type.PHYSICAL
        if not bypass_mitigation:
            amount = self.effects.modify_incoming_damage(amount, damage_type)
            if damage_type == Damage_type.PHYSICAL:
                penetration = min(1, max(0, armor_penetration))
                effective_armor = math.floor(
                    self.get_armor_defense() * (1 - penetration)
                )
                amount = max(0, amount - effective_armor)
            amount = max(0, math.floor(amount))
        self.health = max(0, self.health - amount)
        return old_health - self.health

    def apply_effect(self, effect):
        return self.effects.apply(effect, self)

    def add_effect(self, effect):
        if effect.instant:
            return self.apply_effect(effect)
        return self.effects.add(effect)

    def trigger_turn_end_effects(self):
        return self.effects.on_turn_end(self)

    def trigger_turn_start_effects(self):
        return self.effects.on_turn_start(self)

    def trigger_action_effects(self, action):
        return self.effects.on_action_performed(self, action)

    def is_alive(self):
        return self.health > 0

class Enemy_Rarity(Enum): 
    COMMON = ("Обычный", 1.0, "\033[32m") 
    DANGEROUS = ("Опасный", 1.25, "\033[34m") # Синий
    ELITE = ("Элитный", 1.75, "\035[31m") # Фиолетовый
