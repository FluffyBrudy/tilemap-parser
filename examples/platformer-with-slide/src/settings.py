from pathlib import Path

WIDTH = 1280
HEIGHT = 720
FPS = 60

BLACK = (0, 0, 0)

BASE_PATH = Path(__file__).parent.parent
COLLISION_TILESET_PATH = BASE_PATH / "data" / "collision"
ANIMATION_PATH = BASE_PATH / "data" / "animations"
CHARACTER_COLLISION_PATH = BASE_PATH / "data" / "character_collision"
