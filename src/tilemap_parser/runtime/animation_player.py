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
    render_scale: float = 1.0
    grid_columns: int = 0
    grid_rows: int = 0

    @classmethod
    def load(
        cls,
        json_path: PathLike,
        *,
        spritesheet_path: Optional[PathLike] = None,
        extra_search_base: Optional[Path] = None,
        render_scale: float = 1.0,
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

        tw, th = library.tile_size
        ox, oy = library.grid_offset
        grid_columns = max(1, (surface.get_width() - ox) // tw)
        grid_rows = max(1, (surface.get_height() - oy) // th)

        if render_scale != 1.0:
            if render_scale <= 0:
                raise ValueError(f"render_scale must be > 0, got {render_scale}")
            w, h = surface.get_size()
            sw, sh = int(w * render_scale), int(h * render_scale)
            stw, sth = int(tw * render_scale), int(th * render_scale)
            if sw < 1 or sh < 1 or stw < 1 or sth < 1:
                raise ValueError(f"render_scale {render_scale} produces zero-sized atlas cells")
            if (
                int(ox * render_scale) + grid_columns * stw > sw
                or int(oy * render_scale) + grid_rows * sth > sh
            ):
                raise ValueError(
                    f"render_scale {render_scale} cannot maintain atlas grid cell bounds"
                )
            surface = pygame.transform.scale(surface, (sw, sh))
            library = _scaled_library(library, render_scale)

        return cls(
            library=library,
            surface=surface,
            warnings=warnings,
            json_path=path,
            grid_offset_x=library.grid_offset[0],
            grid_offset_y=library.grid_offset[1],
            render_scale=render_scale,
            grid_columns=grid_columns,
            grid_rows=grid_rows,
        )

    def get_content_bounds(self, clip_name: str) -> Optional[Rect]:
        clip = self.library.get(clip_name)
        if clip is None or not clip.frames:
            return None
        union: Optional[Rect] = None
        for frame in clip.frames:
            surf = self.get_image(frame.variant_id, copy_surface=False)
            if surf is None:
                continue
            rect = surf.get_bounding_rect()
            if rect.width == 0 or rect.height == 0:
                continue
            if union is None:
                union = rect.copy()
            else:
                union.union_ip(rect)
        return union

    def get_image(self, variant_id: int, *, copy_surface: bool = True) -> Optional[Surface]:
        tw, th = self.library.tile_size
        if tw <= 0 or th <= 0 or self.grid_columns <= 0 or self.grid_rows <= 0:
            return None
        col = variant_id % self.grid_columns
        row = variant_id // self.grid_columns
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


def _scaled_library(library: AnimationLibrary, scale: float) -> AnimationLibrary:
    """Return a copy of *library* whose grid geometry is scaled by *scale*.

    Kept in lockstep with the scaled spritesheet surface so that
    :meth:`SpriteAnimationSet.get_image` continues to address cells
    correctly.
    """
    return AnimationLibrary(
        animations=library.animations,
        spritesheet_path=library.spritesheet_path,
        tile_size=(int(library.tile_size[0] * scale), int(library.tile_size[1] * scale)),
        grid_offset=(int(library.grid_offset[0] * scale), int(library.grid_offset[1] * scale)),
        trim_transparent=library.trim_transparent,
    )
