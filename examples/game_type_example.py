"""
Example demonstrating the game_type preset API for CollisionRunner.

Shows how to use from_game_type() for easy setup and validation.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.collision import CollisionCache, RectangleShape
from tilemap_parser.collision_runner import CollisionRunner


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(width=32, height=32)

        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False


def example_platformer():
    """Example: Platformer game setup"""
    print("=== Platformer Example ===")

    cache = CollisionCache()

    runner = CollisionRunner.from_game_type("platformer", cache, tile_size=(32, 32))

    print(f"Game type: platformer")
    print(f"Gravity: {runner.gravity} px/s²")
    print(f"Max fall speed: {runner.max_fall_speed} px/s")
    print(f"Jump strength: {runner.jump_strength} px/s")
    print(f"Mode: {runner.mode.value}")

    runner.gravity = 1000.0
    runner.jump_strength = -500.0

    print(f"\nAfter customization:")
    print(f"Gravity: {runner.gravity} px/s²")
    print(f"Jump strength: {runner.jump_strength} px/s")

    runner.validate_config()
    print("✓ Configuration valid\n")


def example_topdown():
    """Example: Top-down game setup"""
    print("=== Top-Down Example ===")

    cache = CollisionCache()

    runner = CollisionRunner.from_game_type("topdown", cache, tile_size=(16, 16))

    print(f"Game type: topdown")
    print(f"Gravity: {runner.gravity} (no gravity)")
    print(f"Mode: {runner.mode.value}")
    print(f"Friction: {runner.slide_friction}")

    runner.slide_friction = 0.05

    print(f"\nAfter customization:")
    print(f"Friction: {runner.slide_friction} (slippery!)")

    runner.validate_config()
    print("✓ Configuration valid\n")


def example_rpg():
    """Example: RPG game setup"""
    print("=== RPG Example ===")

    cache = CollisionCache()

    runner = CollisionRunner.from_game_type("rpg", cache, tile_size=(32, 32))

    print(f"Game type: rpg")
    print(f"Gravity: {runner.gravity} (no gravity)")
    print(f"Mode: {runner.mode.value}")
    print(f"Snap to grid: {runner.rpg_snap_to_grid}")

    runner.rpg_snap_to_grid = True

    print(f"\nAfter customization:")
    print(f"Snap to grid: {runner.rpg_snap_to_grid}")

    runner.validate_config()
    print("✓ Configuration valid\n")


def example_validation_error():
    """Example: Configuration validation catching errors"""
    print("=== Validation Error Example ===")

    cache = CollisionCache()

    runner = CollisionRunner.from_game_type("platformer", cache, tile_size=(32, 32))

    runner.gravity = 0.0

    print(f"Set gravity to 0 (mistake!)")

    try:
        runner.validate_config()
    except ValueError as e:
        print(f"\n✗ Validation caught the error:")
        print(f"{e}\n")


def example_validation_warning():
    """Example: Configuration validation with warnings"""
    print("=== Validation Warning Example ===")

    cache = CollisionCache()

    runner = CollisionRunner.from_game_type("topdown", cache, tile_size=(32, 32))

    runner.gravity = 800.0

    print(f"Set gravity to 800 for top-down game (unusual)")

    print("\nValidating with strict=False:")
    runner.validate_config(strict=False)
    print("✓ Validation passed with warnings\n")


def example_manual_config():
    """Example: Manual configuration (advanced users)"""
    print("=== Manual Configuration Example ===")

    cache = CollisionCache()

    from tilemap_parser.collision_runner import MovementMode

    runner = CollisionRunner(cache, tile_size=(32, 32), mode=MovementMode.SLIDE)
    runner.gravity = 0.0
    runner.slide_friction = 0.15

    print(f"Manual configuration:")
    print(f"Mode: {runner.mode.value}")
    print(f"Gravity: {runner.gravity}")
    print(f"Friction: {runner.slide_friction}")
    print("✓ Advanced users have full control\n")


if __name__ == "__main__":
    example_platformer()
    example_topdown()
    example_rpg()
    example_validation_error()
    example_validation_warning()
    example_manual_config()

    print("=== Summary ===")
    print("✓ from_game_type() provides easy presets")
    print("✓ Customization is simple after creation")
    print("✓ validate_config() catches configuration mistakes")
    print("✓ Manual configuration still available for advanced users")
