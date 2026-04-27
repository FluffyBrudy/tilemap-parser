"""
Character Collision - Development Mode

USAGE: Run from repository root with local source.

    python examples/03-collision/character_dev.py
"""

import sys
from pathlib import Path

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tilemap_parser.collision import (
    RectangleShape, CircleShape, CapsuleShape,
    CharacterCollision, parse_character_collision,
    load_character_collision
)


def main():
    script_dir = Path(__file__).parent.parent.parent / "examples"
    
    # Method 1: Load from sidecar collision file
    # sprite.png -> sprite.collision.json
    sprite_path = script_dir / "hero.png"
    character_collision = load_character_collision(str(sprite_path))
    
    if character_collision:
        print(f"Character: {character_collision.name}")
        print(f"Properties: {character_collision.properties}")
        
        shape = character_collision.shape
        print(f"\nShape type: {type(shape).__name__}")
        
        if isinstance(shape, RectangleShape):
            print(f"  Size: {shape.width} x {shape.height}")
            print(f"  Offset: {shape.offset}")
            bounds = shape.get_bounds(x=100, y=200)
            print(f"  Bounds at (100, 200): {bounds}")
        elif isinstance(shape, CircleShape):
            print(f"  Radius: {shape.radius}")
            print(f"  Offset: {shape.offset}")
            center = shape.get_center(x=100, y=200)
            print(f"  Center at (100, 200): {center}")
        elif isinstance(shape, CapsuleShape):
            print(f"  Radius: {shape.radius}, Height: {shape.height}")
            print(f"  Offset: {shape.offset}")
            top = shape.get_top_center(x=100, y=200)
            bottom = shape.get_bottom_center(x=100, y=200)
            print(f"  Top center: {top}, Bottom center: {bottom}")
    
    # Method 2: Parse from dict
    collision_data = {
        "name": "CustomCharacter",
        "shape": {
            "type": "rectangle",
            "width": 24.0,
            "height": 32.0,
            "offset": [0.0, 0.0]
        },
        "properties": {
            "speed": 150,
            "jump_strength": -400
        }
    }
    
    custom = parse_character_collision(collision_data)
    print(f"\nCustom character: {custom.name}")
    print(f"Shape: {type(custom.shape).__name__}")
    print(f"Properties: {custom.properties}")


if __name__ == "__main__":
    main()