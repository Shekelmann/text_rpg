"""Art-only settings. Bounds are detected from non-background pixels at load."""
from pathlib import Path

ART_ROOT = Path(__file__).resolve().parent / "pics"
ENEMY_ART = {
    "goblin": {"file": "goblin-level-1-128.png", "scale": 2},
    "wolf": {"file": "wolf-128.png", "scale": 2},
    "likho": {"file": "likho-128.png", "scale": 3},
    "leshy": {"file": "leshy-128.png", "scale": 3},
}
