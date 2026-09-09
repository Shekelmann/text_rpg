"""Rebuild reviewed weapon crops, using nearest-neighbor exclusively.

Run from any directory: python tools/build_weapon_icons.py [axe] [--size 48]
Requires Pillow (only this offline build tool and its tests need it).
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw
from rarity import Rarity
from weapon_icons import ICON_SIZE, WEAPON_ASSETS


# Sheet geometry, not an alternative definition of game rarity.
QUADRANTS = (Rarity.COMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY)
NEAREST = Image.Resampling.NEAREST if hasattr(Image, "Resampling") else Image.NEAREST


def fit_icon(image, box, size=ICON_SIZE):
    """Keep the entire frame, preserve aspect, and center on transparent RGBA."""
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    left, top, right, bottom = box
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError(f"Crop is outside source: {box}")
    crop = image.crop(box).convert("RGBA")
    scale = size / max(crop.size)
    dimensions = tuple(max(1, round(edge * scale)) for edge in crop.size)
    resized = crop.resize(dimensions, resample=NEAREST)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return result


def build_sheet(family, metadata, output_dir, size=ICON_SIZE):
    source = WEAPON_ASSETS / "sources" / metadata["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError(f"Source changed: review crop coordinates first: {source}")
    boxes = metadata["boxes"]
    if len(boxes) != len(QUADRANTS):
        raise ValueError("A sheet must contain four reviewed frame bounds")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with Image.open(source) as image:
        for rarity, box in zip(QUADRANTS, boxes):
            path = output_dir / f"{family}_{rarity.name.lower()}.png"
            fit_icon(image, box, size).save(path, format="PNG")
            paths.append(path)
    return paths


def make_preview(families, output_dir, destination):
    """Nearest-neighbor enlarged review sheet, separate from runtime icons."""
    preview = Image.new("RGB", (700, 35 + len(families) * 165), "#202322")
    draw = ImageDraw.Draw(preview)
    for col, rarity in enumerate(QUADRANTS):
        draw.text((col * 175 + 18, 12), rarity.name, fill="white")
    for row, family in enumerate(families):
        for col, rarity in enumerate(QUADRANTS):
            with Image.open(Path(output_dir) / f"{family}_{rarity.name.lower()}.png") as icon:
                enlarged = icon.convert("RGBA").resize((128, 128), resample=NEAREST)
                xy = (col * 175 + 18, 35 + row * 165)
                preview.paste(enlarged, xy, enlarged)
                draw.text((xy[0], xy[1] + 136), family, fill="white")
    preview.save(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", nargs="*", help="WEAPONS IDs; default: all reviewed sheets")
    parser.add_argument("--size", type=int, default=ICON_SIZE)
    parser.add_argument("--output-dir", type=Path, default=WEAPON_ASSETS / "icons")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((WEAPON_ASSETS / "sheets.json").read_text(encoding="utf-8"))
    families = args.families or list(manifest)
    from objects import WEAPONS
    for family in families:
        if family not in manifest or family not in WEAPONS:
            parser.error(f"Unknown weapon sheet: {family}")
    for family in families:
        paths = build_sheet(family, manifest[family], args.output_dir, args.size)
        print(f"{family}: {len(paths)} icons, {args.size}x{args.size}")
    if args.preview:
        make_preview(families, args.output_dir, args.output_dir.parent / "preview.png")


if __name__ == "__main__":
    main()
