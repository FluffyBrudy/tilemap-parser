"""player.py — the animated player: procedurally generated art + controller.

The spritesheet and its animation JSON are written into ``./generated``
the first time the example runs.  Assets are generated at runtime, so
this example has no external asset dependencies.

The player is a plain class exposing the attributes a collision runner
reads: ``x``, ``y``, ``vx``, ``vy``, ``on_ground`` and
``collision_shape`` — nothing more.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser import AnimationPlayer, RectangleShape, SpriteAnimationSet

PLAYER_W, PLAYER_H = 24, 28
CELL = 32

DURATIONS = {"idle": 450.0, "walk": 120.0, "jump": 500.0}

INK = (20, 25, 35)
BODY = (60, 200, 190)
DARK = (35, 120, 120)
VISOR = (120, 230, 250)

# (legs, blink): each leg is (x, y) of a 4x8 pixel leg within the cell
FRAMES = [
    ([(12, 24), (16, 24)], False),  # 0 idle, eyes open
    ([(12, 24), (16, 24)], True),  # 1 idle, eyes closed
    ([(10, 24), (18, 24)], False),  # 2 walk, stride A
    ([(18, 24), (10, 24)], False),  # 3 walk, stride B
    ([(12, 20), (16, 20)], False),  # 4 jump, legs tucked
]


def build_player_assets(asset_dir: Path) -> Path:
    """Draw the 5-frame spritesheet, write the animation JSON, return its path."""
    asset_dir.mkdir(parents=True, exist_ok=True)

    sheet = pygame.Surface((len(FRAMES) * CELL, CELL), pygame.SRCALPHA)
    for i, (legs, blink) in enumerate(FRAMES):
        x = i * CELL
        for lx, ly in legs:
            pygame.draw.rect(sheet, INK, (x + lx - 1, ly, 6, 10))
            pygame.draw.rect(sheet, DARK, (x + lx, ly, 4, 8))
        pygame.draw.rect(sheet, INK, (x + 9, 7, 14, 18))
        pygame.draw.rect(sheet, BODY, (x + 10, 8, 12, 16))
        pygame.draw.rect(sheet, INK, (x + 11, 1, 10, 9))
        pygame.draw.rect(sheet, BODY, (x + 12, 2, 8, 7))
        pygame.draw.rect(sheet, INK, (x + 13, 3, 6, 5))
        pygame.draw.rect(sheet, VISOR if not blink else DARK, (x + 13, 3, 6, 4))

    sheet_path = asset_dir / "player.png"
    pygame.image.save(sheet, str(sheet_path))

    json_path = asset_dir / "player.anim.json"
    json_path.write_text(
        json.dumps(
            {
                "spritesheet_path": "player.png",
                "tile_size": [CELL, CELL],
                "grid_offset": [0, 0],
                "animations": {
                    name: {
                        "name": name,
                        "frames": [
                            {"variant_id": fid, "duration_ms": DURATIONS[name]}
                            for fid in fids
                        ],
                        "loop": name != "jump",
                    }
                    for name, fids in {"idle": [0, 1], "walk": [2, 3], "jump": [4]}.items()
                },
            },
            indent=2,
        )
    )
    return json_path


class Player:
    """Animated platformer controller (satisfies the sprite protocol)."""

    def __init__(self, x: float, y: float, asset_dir: Path):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.facing = 1  # 1 = right, -1 = left
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFD  # everything except layer 2 (the pillar)
        self.collision_shape = RectangleShape(width=PLAYER_W, height=PLAYER_H)

        anim_set = SpriteAnimationSet.load(build_player_assets(asset_dir))
        self.anims = {
            name: AnimationPlayer(anim_set, name) for name in ("idle", "walk", "jump")
        }
        self._state = None
        self._set_state("idle")

    def _set_state(self, name: str) -> None:
        if name != self._state:
            self._state = name
            self.anims[name].reset()

    def update_animation(self, dt: float) -> None:
        if not self.on_ground:
            self._set_state("jump")
        elif self.vx != 0.0:
            self._set_state("walk")
        else:
            self._set_state("idle")
        self.anims[self._state].update(dt * 1000)

    def draw(self, screen, offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        frame = self.anims[self._state].get_current_image()
        if self.facing < 0:
            frame = pygame.transform.flip(frame, True, False)
        rect = frame.get_rect(
            midbottom=(self.x + PLAYER_W / 2 - offset_x, self.y + PLAYER_H - offset_y)
        )
        screen.blit(frame, rect)
