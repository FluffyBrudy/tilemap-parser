"""
Character Collision - Production Mode

USAGE: Run with tilemap-parser installed.

    pip install tilemap-parser
    python examples/03-collision/character_prod.py
"""

from pathlib import Path

from tilemap_parser.collision import (
    CollisionCache,
    RectangleShape,
    CircleShape,
    CapsuleShape,
)


def main():
    # The editor stores character collision files at:
    #   <data_root>/character_collision/<character_name>.collision.json
    #
    # In your game, data_root comes from settings.json.  Here we point at
    # the bundled example fixtures so the script is runnable out of the box.
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    data_root = examples_dir / "fixtures"

    cache = CollisionCache()

    character_names = ["hero", "enemy", "npc"]
    characters = {}

    for name in character_names:
        collision_path = data_root / "character_collision" / f"{name}.collision.json"
        collision = cache.get_character_collision(collision_path)
        if collision:
            characters[name] = collision
            print(f"Loaded: {collision.name}")
        else:
            print(f"No collision data for: {collision_path}")

    # Create sprite collision shapes programmatically.
    # These are used with CollisionRunner for movement.

    # Player: Rectangle shape
    player_shape = RectangleShape(width=24, height=32, offset=(4, 0))
    print(f"\nPlayer shape bounds at (100, 100): {player_shape.get_bounds(100, 100)}")

    # Enemy: Circle shape
    enemy_shape = CircleShape(radius=16, offset=(0, 0))
    print(f"Enemy center at (100, 100): {enemy_shape.get_center(100, 100)}")

    # Snake: Capsule shape (long and thin)
    snake_shape = CapsuleShape(radius=8, height=48, offset=(0, 0))
    print(f"Snake top: {snake_shape.get_top_center(100, 100)}")
    print(f"Snake bottom: {snake_shape.get_bottom_center(100, 100)}")

    # Use with CollisionRunner
    print("\n--- CollisionRunner Setup ---")
    from tilemap_parser.collision_runner import CollisionRunner

    runner = CollisionRunner.from_game_type("platformer", cache, tile_size=(32, 32))
    print(f"Runner mode: {runner.mode.value}")
    print(f"Gravity: {runner.gravity} px/s²")


if __name__ == "__main__":
    main()
