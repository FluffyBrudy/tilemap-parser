from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pygame
from pygame import Rect, Surface

PathLike = Union[str, Path]


class AnimationParseError(ValueError):
    pass


def _req_dict(v: Any, ctx: str) -> Dict[str, Any]:
    if not isinstance(v, dict):
        raise AnimationParseError(f"{ctx}: expected object")
    return v


def _req_list(v: Any, ctx: str) -> List[Any]:
    if not isinstance(v, list):
        raise AnimationParseError(f"{ctx}: expected array")
    return v


def _req_str(v: Any, ctx: str) -> str:
    if not isinstance(v, str):
        raise AnimationParseError(f"{ctx}: expected string")
    return v


def _coerce_int(v: Any, ctx: str) -> int:
    if isinstance(v, bool):
        raise AnimationParseError(f"{ctx}: expected int")
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v, 10)
        except ValueError as e:
            raise AnimationParseError(f"{ctx}: expected int") from e
    raise AnimationParseError(f"{ctx}: expected int")


def _coerce_float(v: Any, ctx: str) -> float:
    if isinstance(v, bool):
        raise AnimationParseError(f"{ctx}: expected number")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError as e:
            raise AnimationParseError(f"{ctx}: expected number") from e
    raise AnimationParseError(f"{ctx}: expected number")


@dataclass
class AnimationMarker:
    name: str
    frame_index: int


@dataclass
class AnimationFrame:
    variant_id: int
    duration_ms: float = 100.0


@dataclass
class AnimationClip:
    name: str
    frames: List[AnimationFrame] = field(default_factory=list)
    loop: bool = True
    fps: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    markers: List[AnimationMarker] = field(default_factory=list)

    def frame_count(self) -> int:
        return len(self.frames)

    def total_duration_ms(self) -> float:
        return sum(frame.duration_ms for frame in self.frames)

    def clamp_markers(self) -> None:
        count = len(self.frames)
        if count == 0:
            self.markers.clear()
            return
        for marker in self.markers:
            marker.frame_index = max(0, min(marker.frame_index, count - 1))


@dataclass
class AnimationLibrary:
    animations: Dict[str, AnimationClip] = field(default_factory=dict)
    spritesheet_path: Optional[str] = None
    tile_size: Tuple[int, int] = (32, 32)

    def get(self, name: str) -> Optional[AnimationClip]:
        return self.animations.get(name)


def _parse_marker(d: Dict[str, Any], ctx: str) -> AnimationMarker:
    return AnimationMarker(name=_req_str(d.get("name"), f"{ctx}.name"), frame_index=_coerce_int(d.get("frame_index"), f"{ctx}.frame_index"))


def _parse_frame(d: Dict[str, Any], ctx: str) -> AnimationFrame:
    return AnimationFrame(variant_id=_coerce_int(d.get("variant_id"), f"{ctx}.variant_id"), duration_ms=_coerce_float(d.get("duration_ms", 100.0), f"{ctx}.duration_ms"))


def _parse_animation(name: str, d: Dict[str, Any], ctx: str) -> AnimationClip:
    frames_raw = _req_list(d.get("frames", []), f"{ctx}.frames")
    frames = [_parse_frame(_req_dict(f, f"{ctx}.frames[{i}]"), f"{ctx}.frames[{i}]") for i, f in enumerate(frames_raw)]

    metadata_raw = d.get("metadata")
    if metadata_raw is None:
        metadata: Dict[str, Any] = {}
    elif isinstance(metadata_raw, dict):
        metadata = dict(metadata_raw)
    else:
        raise AnimationParseError(f"{ctx}.metadata: expected object or null")

    markers: List[AnimationMarker] = []
    markers_raw = d.get("markers")
    if markers_raw is not None:
        for i, marker in enumerate(_req_list(markers_raw, f"{ctx}.markers")):
            markers.append(_parse_marker(_req_dict(marker, f"{ctx}.markers[{i}]"), f"{ctx}.markers[{i}]"))

    clip = AnimationClip(
        name=_req_str(d.get("name", name), f"{ctx}.name"),
        frames=frames,
        loop=bool(d.get("loop", True)),
        fps=_coerce_float(d.get("fps", 60.0), f"{ctx}.fps"),
        metadata=metadata,
        markers=markers,
    )
    clip.clamp_markers()
    return clip


def parse_animation_dict(data: Dict[str, Any]) -> AnimationLibrary:
    root = _req_dict(data, "root")
    spritesheet = root.get("spritesheet_path")
    spritesheet_path = _req_str(spritesheet, "spritesheet_path") if spritesheet is not None else None

    tile_size_raw = _req_list(root.get("tile_size", [32, 32]), "tile_size")
    if len(tile_size_raw) != 2:
        raise AnimationParseError("tile_size: expected [w, h]")
    tw = _coerce_int(tile_size_raw[0], "tile_size[0]")
    th = _coerce_int(tile_size_raw[1], "tile_size[1]")
    if tw < 1 or th < 1:
        raise AnimationParseError("tile_size: width and height must be >= 1")

    animations_raw = _req_dict(root.get("animations", {}), "animations")
    animations: Dict[str, AnimationClip] = {}
    for key, value in animations_raw.items():
        k = str(key)
        animations[k] = _parse_animation(k, _req_dict(value, f"animations[{k!r}]"), f"animations[{k!r}]")

    return AnimationLibrary(animations=animations, spritesheet_path=spritesheet_path, tile_size=(tw, th))


def parse_animation_json(text: str) -> AnimationLibrary:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise AnimationParseError(f"Invalid JSON: {e}") from e
    return parse_animation_dict(_req_dict(payload, "root"))


def parse_animation_file(path: PathLike) -> AnimationLibrary:
    p = Path(path)
    if not p.is_file():
        raise AnimationParseError(f"Not a file: {p}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise AnimationParseError(f"Cannot read {p}: {e}") from e
    return parse_animation_json(text)


@dataclass
class SpriteAnimationSet:
    library: AnimationLibrary
    surface: Surface
    warnings: List[str]
    json_path: Optional[Path] = None
    grid_offset_x: int = 0
    grid_offset_y: int = 0

    @classmethod
    def load(
        cls,
        json_path: PathLike,
        *,
        spritesheet_path: Optional[PathLike] = None,
        extra_search_base: Optional[Path] = None,
    ) -> "SpriteAnimationSet":
        path = Path(json_path)
        library = parse_animation_file(path)
        warnings: List[str] = []

        if not pygame.get_init():
            pygame.init()

        sheet_ref = spritesheet_path if spritesheet_path is not None else library.spritesheet_path
        if sheet_ref is None:
            raise AnimationParseError("No spritesheet_path in JSON and none passed to load()")

        image_path = Path(sheet_ref)
        if not image_path.is_absolute():
            candidate = (path.parent / image_path).resolve()
            if candidate.is_file():
                image_path = candidate
            elif extra_search_base is not None:
                extra = (Path(extra_search_base) / str(sheet_ref)).resolve()
                image_path = extra if extra.is_file() else candidate
            else:
                image_path = candidate

        if not image_path.is_file():
            raise AnimationParseError(f"Spritesheet not found: {sheet_ref!r} (tried {image_path})")

        try:
            surface = pygame.image.load(str(image_path)).convert_alpha()
        except pygame.error as e:
            raise AnimationParseError(f"Failed to load image {image_path}: {e}") from e

        return cls(library=library, surface=surface, warnings=warnings, json_path=path)

    def get_image(self, variant_id: int, *, copy_surface: bool = True) -> Optional[Surface]:
        tw, th = self.library.tile_size
        if tw <= 0 or th <= 0:
            return None
        available_w = self.surface.get_width() - self.grid_offset_x
        available_h = self.surface.get_height() - self.grid_offset_y
        if available_w < tw or available_h < th:
            return None
        cols = max(1, available_w // tw)
        col = variant_id % cols
        row = variant_id // cols
        src = Rect(self.grid_offset_x + col * tw, self.grid_offset_y + row * th, tw, th)
        if not self.surface.get_rect().contains(src):
            return None
        cel = self.surface.subsurface(src)
        return cel.copy() if copy_surface else cel


class AnimationPlayer:
    def __init__(self, animation_set: SpriteAnimationSet, animation_name: str) -> None:
        self.animation_set = animation_set
        self.animation_name = animation_name
        self._elapsed_in_frame = 0.0
        self._frame_index = 0
        self._finished = False
        self._frame_cache: Dict[int, Optional[Surface]] = {}

    @property
    def clip(self) -> Optional[AnimationClip]:
        return self.animation_set.library.get(self.animation_name)

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def frame_index(self) -> int:
        return self._frame_index

    def reset(self) -> None:
        self._elapsed_in_frame = 0.0
        self._frame_index = 0
        self._finished = False

    def update(self, dt_ms: float) -> None:
        clip = self.clip
        if clip is None or not clip.frames:
            self._finished = True
            return
        if self._finished:
            return
        self._elapsed_in_frame += dt_ms
        while self._elapsed_in_frame >= clip.frames[self._frame_index].duration_ms:
            self._elapsed_in_frame -= clip.frames[self._frame_index].duration_ms
            self._frame_index += 1
            if self._frame_index >= len(clip.frames):
                if clip.loop:
                    self._frame_index = 0
                else:
                    self._frame_index = len(clip.frames) - 1
                    self._finished = True
                    break

    def get_current_image(self) -> Optional[Surface]:
        clip = self.clip
        if clip is None or not clip.frames:
            return None
        variant = clip.frames[self._frame_index].variant_id
        if variant not in self._frame_cache:
            self._frame_cache[variant] = self.animation_set.get_image(variant, copy_surface=True)
        return self._frame_cache[variant]
