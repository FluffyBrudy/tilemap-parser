from pathlib import Path

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
