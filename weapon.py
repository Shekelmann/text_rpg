import math
from item import Item
from rarity import Rarity
from affix import AffixType, AFFIX_COUNTS, apply_modifiers, validate_affixes, generate_affixes
from damage import Damage_type

class Weapon(Item):
    def __init__(
        self,
        name,
        min_damage,
        max_damage,
        crit_chance,
        weapon_type,
        damage_type,
        price=1,
        rarity=Rarity.COMMON,
        affixes=(),
        *,
        icon_id=None,
    ):
        
        super().__init__(
            name,
            item_type="weapon",
            use_in_combat=False,
            price=price,
            rarity=rarity,
        ) # Вызов родительского класса Item
        self.is_weapon = True # Устанавливаем флаг
        self.icon_id = icon_id

        self.name = name
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.crit_chance = crit_chance
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.set_affixes(affixes)

    @property
    def affixes(self):
        return self._affixes

    @property
    def display_name(self):
        prefixes = [a.name for a in self.affixes if a.type == AffixType.PREFIX]
        suffixes = [a.name for a in self.affixes if a.type == AffixType.SUFFIX]
        base = self.name[:1].lower() + self.name[1:] if prefixes else self.name
        return " ".join((*prefixes, base, *suffixes))

    def set_affixes(self, affixes):
        affixes = tuple(affixes)
        validate_affixes(affixes)
        if affixes:
            if self.rarity not in AFFIX_COUNTS:
                raise ValueError("Affixes are not implemented for this rarity")
            if len(affixes) > AFFIX_COUNTS[self.rarity][1]:
                raise ValueError("Too many affixes for the item rarity")
        self._affixes = affixes

    def add_affix(self, affix):
        self.set_affixes((*self.affixes, affix))

    def remove_affix(self, affix):
        remaining = list(self.affixes)
        remaining.remove(affix)
        self.set_affixes(remaining)

    def generate_affixes(self, pool, rng=None):
        self.set_affixes(generate_affixes(self.rarity, pool, rng))
        return self.affixes

    def get_final_stat(self, target, base, source=None, defender=None):
        modifiers = (modifier for affix in self.affixes for modifier in affix.modifiers)
        return apply_modifiers(base, target, modifiers, source, defender)

    def _final_damage(self, base, source=None, defender=None):
        # Physical bonuses apply only to physical weapons, before character bonuses.
        value = base
        if self.damage_type == Damage_type.PHYSICAL:
            value = self.get_final_stat("physical_damage", base, source, defender)
        return max(0, math.floor(round(value, 10)))

    def get_damage_range(self, source=None, defender=None):
        return (self._final_damage(self.min_damage, source, defender),
                self._final_damage(self.max_damage, source, defender))

    def on_hit(self, target, successful=True):
        if not successful:
            return
        for affix in self.affixes:
            for effect in affix.effects:
                target.add_effect(effect.create())

    @property
    def final_min_damage(self):
        return self._final_damage(self.min_damage)

    @property
    def final_max_damage(self):
        return self._final_damage(self.max_damage)

    @property
    def final_crit_chance(self):
        return min(1, max(0, self.get_final_stat("crit_chance", self.crit_chance)))
