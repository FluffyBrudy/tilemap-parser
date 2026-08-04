"""crate.py — kinematic bodies: how a push works.

Bodies never move themselves.  A ``mode="kinematic"`` body is moved by
the game with an explicit velocity, resolved through the same collision
lane as the player: ``move_grounded(crate, None, None, dt,
velocity=(vx, 0))``.  Tiles and other bodies stop it in that one call.
"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

PUSH_SPEED = 260.0


def crates(world):
    """All kinematic bodies in the world (the pushable ones)."""
    return [b for b in world.bodies if b.mode == "kinematic"]


def body_ahead(world, sprite, axis, probe=8.0):
    """Find the body the sprite is pressed against.

    The runner stops a sprite just *short* of a body (a sub-pixel skin
    gap), so a resting-position ``collides_with_body`` check can miss
    it.  Probe a few pixels into the push direction instead.
    """
    s = copy.copy(sprite)
    s.x = sprite.x + axis * probe
    return world.collides_with_body(s)


def push(runner, world, dt):
    """Give every sliding crate one frame of velocity, collision-resolved."""
    for crate in crates(world):
        if crate.vx:
            result = runner.move_grounded(
                crate, None, None, dt, velocity=(crate.vx, 0.0)
            )
            if result.hit_wall_x:
                crate.vx = 0.0
            else:
                crate.vx *= 0.9
                if abs(crate.vx) < 1.0:
                    crate.vx = 0.0
