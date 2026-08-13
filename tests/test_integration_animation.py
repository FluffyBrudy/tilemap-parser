from pathlib import Path

import json

import pygame
import pytest

from tilemap_parser import (
    AnimationLibrary,
    AnimationPlayer,
    AnimationClip,
    SpriteAnimationSet,
    parse_animation_file,
)

PROJECT_ROOT = Path(__file__).parent.parent
PLAYER_ANIM_PATH = (
    PROJECT_ROOT
    / "examples"
    / "platformer"
    / "src"
    / "data"
    / "animations"
    / "player.animation.json"
)
WATERFALL_ANIM_PATH = (
    PROJECT_ROOT
    / "examples"
    / "platformer"
    / "src"
    / "data"
    / "animations"
    / "waterfall.anim.json"
)


class TestParseRealAnimationFile:
    def test_player_has_six_clips(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        assert len(library.animations) == 6

    def test_player_animation_names(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        assert set(library.animations.keys()) == {"idle", "walk", "jump", "attack", "hurt", "dash"}

    def test_idle_has_six_frames(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        clip = library.get("idle")
        assert clip is not None
        assert len(clip.frames) == 6
        assert clip.loop is True

    def test_walk_has_eight_frames(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        clip = library.get("walk")
        assert clip is not None
        assert len(clip.frames) == 8
        assert clip.loop is True

    def test_jump_is_non_looping(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        clip = library.get("jump")
        assert clip is not None
        assert clip.loop is False

    def test_hurt_has_four_frames_at_30_fps(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        clip = library.get("hurt")
        assert clip is not None
        assert len(clip.frames) == 4
        assert clip.fps == 30.0

    def test_spritesheet_path_and_tile_size(self):
        library = parse_animation_file(PLAYER_ANIM_PATH)
        assert library.spritesheet_path is not None
        assert library.tile_size == (150, 60)
        assert library.grid_offset == (0, 0)

    def test_waterfall_animation(self):
        library = parse_animation_file(WATERFALL_ANIM_PATH)
        assert "default" in library.animations
        clip = library.get("default")
        assert clip is not None
        assert len(clip.frames) == 8
        assert clip.loop is True


class TestSpriteAnimationSetLoad:
    def test_load_player_animation_set(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        assert anim_set.library is not None
        assert anim_set.surface is not None
        assert anim_set.surface.get_width() > 0
        assert len(anim_set.warnings) == 0
        assert anim_set.json_path == PLAYER_ANIM_PATH

    def test_get_image_returns_surface(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        img = anim_set.get_image(0)
        assert img is not None
        assert img.get_width() == 150
        assert img.get_height() == 60

    def test_get_image_with_variant_id(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        img = anim_set.get_image(8)
        assert img is not None

    def test_get_content_bounds_idle(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        bounds = anim_set.get_content_bounds("idle")
        assert bounds is not None
        assert bounds.width > 0
        assert bounds.height > 0

    def test_get_content_bounds_nonexistent_clip(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        bounds = anim_set.get_content_bounds("nonexistent")
        assert bounds is None

    def test_load_with_render_scale(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=2.0)
        assert anim_set.render_scale == 2.0
        assert anim_set.surface.get_width() == 2400
        assert anim_set.surface.get_height() == 840
        assert anim_set.library.tile_size == (300, 120)
        assert anim_set.library.grid_offset == (0, 0)
        assert anim_set.grid_offset_x == 0

    def test_render_scale_one_matches_default(self):
        default = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        explicit = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=1.0)
        assert explicit.render_scale == 1.0
        assert explicit.surface.get_size() == default.surface.get_size()
        assert explicit.library.tile_size == default.library.tile_size

    def test_get_image_scaled_by_render_scale(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=2.0)
        img = anim_set.get_image(0)
        assert img is not None
        assert img.get_width() == 300
        assert img.get_height() == 120

    def test_get_image_cell_lookup_still_valid_at_scale(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=2.0)
        img = anim_set.get_image(8)
        assert img is not None
        assert img.get_size() == (300, 120)

    def test_get_content_bounds_scaled(self):
        base = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        scaled = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=3.0)
        base_bounds = base.get_content_bounds("idle")
        scaled_bounds = scaled.get_content_bounds("idle")
        assert base_bounds is not None and scaled_bounds is not None
        assert scaled_bounds.width == base_bounds.width * 3
        assert scaled_bounds.height == base_bounds.height * 3
        assert scaled_bounds.x == base_bounds.x * 3
        assert scaled_bounds.y == base_bounds.y * 3

    def test_invalid_render_scale_raises(self):
        with pytest.raises(ValueError):
            SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=0)

    def test_zero_sized_scaled_cells_rejected(self):
        for bad in (0.01, 0.0005):
            with pytest.raises(ValueError, match="zero-sized"):
                SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=bad)

    def test_animation_player_frames_scaled(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH, render_scale=2.0)
        player = AnimationPlayer(anim_set, "idle")
        img = player.get_current_image()
        assert img is not None
        assert img.get_size() == (300, 120)


def _write_offset_atlas(tmp_path: Path, cols: int, rows: int):
    """Write a synthetic atlas with a nonzero grid offset and solid per-cell colors."""
    tile = 8
    ox, oy = 1, 1
    w, h = ox + cols * tile, oy + rows * tile
    sheet = pygame.Surface((w, h))
    colors = {}
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            color = (
                (20 + idx * 7) % 256,
                (40 + idx * 13) % 256,
                (60 + idx * 29) % 256,
            )
            colors[idx] = color
            sheet.fill(color, (ox + col * tile, oy + row * tile, tile, tile))
    sheet.fill((250, 250, 250), (0, 0, w, oy))
    sheet.fill((250, 250, 250), (0, 0, ox, h))
    png_path = tmp_path / "atlas.png"
    pygame.image.save(sheet, str(png_path))
    json_path = tmp_path / "atlas.animation.json"
    json_path.write_text(
        json.dumps(
            {
                "spritesheet_path": str(png_path),
                "tile_size": [tile, tile],
                "grid_offset": [ox, oy],
                "trim_transparent": False,
                "animations": {
                    "test": {
                        "name": "test",
                        "frames": [{"variant_id": 0, "duration_ms": 100.0}],
                        "loop": True,
                    }
                },
            }
        )
    )
    return colors


class TestFractionalScaleWithOffset:
    def test_downscale_0_6_returns_correct_cell(self, tmp_path):
        colors = _write_offset_atlas(tmp_path, cols=5, rows=3)
        anim_set = SpriteAnimationSet.load(
            tmp_path / "atlas.animation.json", render_scale=0.6
        )
        for variant in (0, 5, 6):
            img = anim_set.get_image(variant)
            assert img is not None
            center = img.get_at((img.get_width() // 2, img.get_height() // 2))[:3]
            assert center == colors[variant]

    def test_upscale_1_1_returns_correct_cell(self, tmp_path):
        colors = _write_offset_atlas(tmp_path, cols=12, rows=3)
        anim_set = SpriteAnimationSet.load(
            tmp_path / "atlas.animation.json", render_scale=1.1
        )
        for variant in (0, 12, 13):
            img = anim_set.get_image(variant)
            assert img is not None
            center = img.get_at((img.get_width() // 2, img.get_height() // 2))[:3]
            assert center == colors[variant]


class TestAnimationPlayerPlayback:
    def test_initial_state(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        assert player.animation_name == "idle"
        assert player.frame_index == 0
        assert player.finished is False
        assert player.clip is not None
        assert player.clip.name == "idle"

    def test_update_advances_frame(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        player.update(100.0)
        assert player.frame_index == 1

    def test_update_advances_past_frame_boundary(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        player.update(250.0)
        assert player.frame_index == 2

    def test_loop_wraps_around(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        player.update(100.0 * 6)
        assert player.frame_index == 0
        assert player.finished is False

    def test_non_looping_animation_finishes(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "jump")
        player.update(100.0 * 7)
        assert player.finished is True
        assert player.frame_index == 6

    def test_get_current_image(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        img = player.get_current_image()
        assert img is not None
        assert img.get_width() == 150
        assert img.get_height() == 60

    def test_reset(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        player.update(200.0)
        assert player.frame_index == 2
        player.reset()
        assert player.frame_index == 0
        assert player.finished is False

    def test_advance_through_all_frames(self):
        anim_set = SpriteAnimationSet.load(PLAYER_ANIM_PATH)
        player = AnimationPlayer(anim_set, "idle")
        frames_seen = []
        for _ in range(12):
            frames_seen.append(player.frame_index)
            player.update(100.0)
        assert frames_seen == [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]
