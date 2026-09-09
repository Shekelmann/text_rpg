import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image

from objects import ITEMS, WEAPONS, STARTER_WEAPON, create_item, generate_starting_weapons, generate_chest_reward
from rarity import Rarity
from weapon import Weapon
from weapon_icons import ICON_SIZE, WEAPON_ASSETS, weapon_icon_path
from tools.build_weapon_icons import build_sheet, fit_icon, QUADRANTS


class TestWeaponIconAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((WEAPON_ASSETS / "sheets.json").read_text(encoding="utf-8"))

    def test_all_registered_families_and_rarities_have_icons(self):
        self.assertEqual(set(self.manifest), set(WEAPONS))
        self.assertEqual(set(QUADRANTS), set(Rarity))
        expected = {f"{family}_{rarity.name.lower()}.png" for family in WEAPONS for rarity in Rarity}
        self.assertEqual({p.name for p in (WEAPON_ASSETS / "icons").glob("*.png")}, expected)

    def test_source_hashes_sizes_and_exact_nearest_samples(self):
        for family, metadata in self.manifest.items():
            source_path = WEAPON_ASSETS / "sources" / metadata["source"]
            self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), metadata["sha256"])
            with Image.open(source_path) as source:
                for rarity, box in zip(QUADRANTS, metadata["boxes"]):
                    with self.subTest(family=family, rarity=rarity):
                        with Image.open(weapon_icon_path(family, rarity)) as icon:
                            self.assertEqual(icon.format, "PNG")
                            self.assertEqual(icon.size, (ICON_SIZE, ICON_SIZE))
                            crop = source.crop(box).convert("RGBA")
                            # Independent pixel-center nearest-neighbor reconstruction:
                            # every non-padding pixel must be an unchanged source pixel.
                            scale = ICON_SIZE / max(crop.size)
                            width, height = (max(1, round(v * scale)) for v in crop.size)
                            xoff, yoff = (ICON_SIZE - width) // 2, (ICON_SIZE - height) // 2
                            for y in range(ICON_SIZE):
                                for x in range(ICON_SIZE):
                                    if xoff <= x < xoff + width and yoff <= y < yoff + height:
                                        sx = (x - xoff + 0.5) * crop.width / width
                                        sy = (y - yoff + 0.5) * crop.height / height
                                        # Exact half-way samples may choose either neighbor
                                        # due to Pillow's floating-point stepping. Neither
                                        # choice may blend the two pixels.
                                        expected = {
                                            crop.getpixel((min(crop.width - 1, int(sx + dx)),
                                                           min(crop.height - 1, int(sy + dy))))
                                            for dx in (-1e-9, 1e-9) for dy in (-1e-9, 1e-9)
                                        }
                                    else:
                                        expected = {(0, 0, 0, 0)}
                                    self.assertIn(icon.getpixel((x, y)), expected)

    def test_non_square_crop_is_fitted_not_stretched(self):
        source = Image.new("RGBA", (100, 80), "red")
        for size in (64, 48):
            result = fit_icon(source, (10, 10, 90, 50), size)
            self.assertEqual(result.size, (size, size))
            self.assertEqual(result.getbbox(), (0, size // 4, size, 3 * size // 4))
            self.assertEqual(set(result.getdata()), {(255, 0, 0, 255), (0, 0, 0, 0)})

    def test_invalid_crop_and_size_fail(self):
        source = Image.new("RGB", (20, 20))
        for box in ((-1, 0, 10, 10), (0, 0, 21, 20), (10, 0, 5, 10)):
            with self.assertRaises(ValueError):
                fit_icon(source, box)
        with self.assertRaises(ValueError):
            fit_icon(source, (0, 0, 20, 20), 0)

    def test_rebuild_at_48_and_changed_source_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = build_sheet("axe", self.manifest["axe"], folder, size=48)
            self.assertEqual(len(paths), 4)
            for path in paths:
                with Image.open(path) as icon:
                    self.assertEqual(icon.size, (48, 48))
            changed = dict(self.manifest["axe"], sha256="invalid")
            with self.assertRaises(ValueError):
                build_sheet("axe", changed, folder)


class TestWeaponIconLookup(unittest.TestCase):
    def test_registry_aliases_and_created_items_retain_family(self):
        for item_id, template in ITEMS.items():
            if not isinstance(template, Weapon):
                continue
            weapon = create_item(item_id)
            self.assertEqual(weapon.icon_id, template.icon_id)
            for rarity in Rarity:
                weapon.rarity = rarity
                self.assertEqual(weapon_icon_path(weapon), weapon_icon_path(item_id, rarity))
                self.assertEqual(weapon_icon_path(weapon).name,
                                 f"{template.icon_id}_{rarity.name.lower()}.png")

    def test_starter_random_weapons_and_chests_retain_lookup(self):
        self.assertEqual(weapon_icon_path(STARTER_WEAPON), weapon_icon_path("sword", Rarity.COMMON))
        for seed in range(15):
            weapons = generate_starting_weapons(random.Random(seed))
            weapons.append(generate_chest_reward((1, 2), random.Random(seed))["weapon"])
            for weapon in weapons:
                self.assertIsNotNone(weapon_icon_path(weapon))
                original_rarity = weapon.rarity
                self.assertIsNotNone(weapon_icon_path(weapon, Rarity.LEGENDARY))
                self.assertIs(weapon.rarity, original_rarity)

    def test_unknown_items_do_not_get_an_incorrect_icon(self):
        self.assertIsNone(weapon_icon_path("not_a_weapon"))
        self.assertIsNone(weapon_icon_path("heal"))
        with self.assertRaises(TypeError):
            weapon_icon_path("axe", "RARE")


if __name__ == "__main__":
    unittest.main()
