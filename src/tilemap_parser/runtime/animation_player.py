from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import pygame
from pygame import Rect, Surface

from ..parser.animation import AnimationLibrary, AnimationParseError, parse_animation_file

PathLike = Union[str, Path]


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

        return cls(
            library=library,
            surface=surface,
            warnings=warnings,
            json_path=path,
            grid_offset_x=library.grid_offset[0],
            grid_offset_y=library.grid_offset[1],
        )

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
        if self.library.trim_transparent:
            brect = cel.get_bounding_rect()
            if brect:
                cel = cel.subsurface(brect)
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
