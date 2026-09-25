from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pygame
from pygame import Rect, Surface, transform

from ..parser.tileanim import (
    ANIM_CLIP_KEY,
    TileAnimClip,
    _frame_index_at,
    load_tile_anim_file,
    resolve_clip_sheet,
)
from .map_loader import TilemapData

CHUNK_SIZE = 32

PathLike = str | Path

_FLIP_H = 1
_FLIP_V = 2
_FLIP_D = 4


def _tile_flip_flags(tile) -> int:
    """Encode a parsed tile's flip bools to a bitmask (0 when unflipped)."""
    return (
        (_FLIP_H if getattr(tile, "flip_h", False) else 0)
        | (_FLIP_V if getattr(tile, "flip_v", False) else 0)
        | (_FLIP_D if getattr(tile, "flip_d", False) else 0)
    )


def _apply_tile_flip(surf: Surface, flip_flags: int) -> Surface:
    """Mirror/transpose a tile surface per flip flags (Tiled order).

    Diagonal transpose first, then horizontal / vertical mirrors — the same
    convention as the collision ``flip_vertices``.  Transpose is
    ``rotate(90)`` + vertical flip, which holds for square tiles; non-square
    transposed tiles are best-effort (dims swap, grid blit unchanged).
    """
    if flip_flags & _FLIP_D:
        surf = transform.flip(transform.rotate(surf, 90), False, True)
    return transform.flip(
        surf,
        bool(flip_flags & _FLIP_H),
        bool(flip_flags & _FLIP_V),
    )


@dataclass(frozen=True)
class LayerRenderStats:
    drawn_tiles: int
    skipped_tiles: int
    visible_layers: int


class TileLayerRenderer:
    def __init__(
        self,
        data: TilemapData,
        *,
        include_hidden_layers: bool = False,
        tile_clips: Mapping[str, TileAnimClip] | PathLike | Sequence[PathLike] | None = None,
        clip_property: str | None = ANIM_CLIP_KEY,
        load_optional_anim: str | None = None,
    ) -> None:
        self.data = data
        self.tile_layers = data.get_tile_layers_dict(include_hidden=include_hidden_layers)
        self._sorted_layer_ids = sorted(
            self.tile_layers.keys(),
            key=lambda lid: (self.tile_layers[lid].z_index, lid),
        )

        self._variant_cache: dict[tuple[int, int], Surface | None] = {}
        self.warnings: list[str] = []
        self.clip_property = clip_property
        self.load_optional_anim = load_optional_anim
        self._clips = self._normalize_clips(tile_clips)
        self._clip_frames: dict[str, tuple[tuple[int | None, int], ...]] = {}
        self._clip_cells: dict[int, dict[tuple[int, int], str]] = {}
        self._stride_off: set[tuple[int, int, int]] = set()
        self._build_anim_index()

        self._tile_w, self._tile_h = data.tile_size
        self._rs = data.render_scale
        if self._rs <= 0:
            raise ValueError(f"render_scale must be positive, got {self._rs}")
        self._eff_w = int(self._tile_w * self._rs)
        self._eff_h = int(self._tile_h * self._rs)
        if self._eff_w <= 0 or self._eff_h <= 0:
            raise ValueError(
                f"effective tile size ({self._eff_w}, {self._eff_h}) must be positive; "
                f"got tile_size=({self._tile_w}, {self._tile_h}) render_scale={self._rs}"
            )

        self._tileset_animations: dict[int, dict] = {}
        for ts_idx, ts in enumerate(data.parsed.tilesets):
            if ts.animation is not None:
                self._tileset_animations[ts_idx] = {
                    "frame_count": ts.animation.frame_count,
                    "frame_duration_ms": ts.animation.frame_duration_ms,
                    "frame_stride": ts.animation.frame_stride,
                    "loop": ts.animation.loop,
                    "animation_mode": ts.animation.animation_mode,
                }

        self._layer_chunks: dict[int, dict[tuple[int, int], list[tuple[int, int]]]] = {}
        for layer_id, layer in self.tile_layers.items():
            chunks: dict[tuple[int, int], list[tuple[int, int]]] = {}
            for (x, y), tile in layer.tiles.items():
                if not isinstance(tile.ttype, int):
                    continue
                cx, cy = x // CHUNK_SIZE, y // CHUNK_SIZE
                chunk_key = (cx, cy)
                if chunk_key not in chunks:
                    chunks[chunk_key] = []
                chunks[chunk_key].append((x, y))
            self._layer_chunks[layer_id] = chunks

    def _normalize_clips(
        self,
        tile_clips: Mapping[str, TileAnimClip] | PathLike | Sequence[PathLike] | None,
    ) -> dict[str, TileAnimClip]:
        if tile_clips is None:
            return {}
        if isinstance(tile_clips, Mapping):
            return dict(tile_clips)
        paths = [tile_clips] if isinstance(tile_clips, (str, Path)) else list(tile_clips)
        merged: dict[str, TileAnimClip] = {}
        for p in paths:
            loaded = load_tile_anim_file(p)
            if not loaded:
                self.warnings.append(f"tile_clips: no clips loaded from {p}")
                continue
            for name, clip in loaded.items():
                if name in merged:
                    self.warnings.append(f"tile_clips: duplicate clip {name!r} from {p} ignored")
                    continue
                merged[name] = clip
        return merged

    def _build_anim_index(self) -> None:
        paths = [getattr(ts, "path", "") or "" for ts in self.data.parsed.tilesets]
        for name, clip in self._clips.items():
            if not clip.frames:
                self.warnings.append(f"tile_clips: clip {name!r} has no playable frames")
                continue
            resolved = tuple((resolve_clip_sheet(paths, f.sheet), f.variant) for f in clip.frames)
            if all(t is None for t, _ in resolved):
                self.warnings.append(f"tile_clips: clip {name!r} sheets match no tileset")
                continue
            for i, (t, v) in enumerate(resolved):
                if t is None:
                    self.warnings.append(
                        f"tile_clips: clip {name!r} frame {i} sheet {clip.frames[i].sheet!r} "
                        f"matches no tileset; that timestamp falls back to static"
                    )
            self._clip_frames[name] = resolved
            for t, v in resolved:
                if t is not None and self.data.get_tile_surface(t, v) is None:
                    self.warnings.append(f"tile_clips: clip {name!r} frame {(t, v)} is outside its sheet")
                    break
        warned_unknown: set[str] = set()
        for layer_id, layer in self.tile_layers.items():
            cells: dict[tuple[int, int], str] = {}
            for (x, y), tile in layer.tiles.items():
                if not isinstance(tile.ttype, int):
                    continue
                props = self.data.get_tile_properties(tile.ttype, tile.variant, tile.properties)
                if self.clip_property is not None:
                    clip_name = props.get(self.clip_property)
                    if isinstance(clip_name, str) and clip_name:
                        if clip_name in self._clip_frames:
                            cells[(x, y)] = clip_name
                        elif clip_name not in warned_unknown:
                            warned_unknown.add(clip_name)
                            self.warnings.append(f"tile_clips: unknown clip {clip_name!r} on {(x, y)}; static")
                if self.load_optional_anim is not None and not props.get(self.load_optional_anim):
                    self._stride_off.add((layer_id, x, y))
            if cells:
                self._clip_cells[layer_id] = cells

    def get_layer_dict(self) -> dict[int, object]:
        return dict(self.tile_layers)

    def _get_cached_variant(self, ttype: int, variant: int, flip_flags: int = 0) -> Surface | None:
        key = (ttype, variant, flip_flags)
        if key not in self._variant_cache:
            cell = self.data.get_tile_surface(ttype, variant, copy_surface=True)
            if cell is not None and self._rs != 1.0:
                cell = transform.scale(cell, (self._eff_w, self._eff_h))
            if cell is not None and flip_flags:
                cell = _apply_tile_flip(cell, flip_flags)
            self._variant_cache[key] = cell
        return self._variant_cache[key]

    def warm_cache(self) -> None:
        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            for (x, y), tile in layer.tiles.items():
                if not isinstance(tile.ttype, int):
                    continue
                flags = _tile_flip_flags(tile)
                anim = self._tileset_animations.get(tile.ttype)
                if anim is not None and (layer_id, x, y) not in self._stride_off:
                    frame_count = anim["frame_count"]
                    stride = anim["frame_stride"]
                    for f in range(frame_count):
                        self._get_cached_variant(tile.ttype, tile.variant + f * stride, flags)
                else:
                    self._get_cached_variant(tile.ttype, tile.variant, flags)
        for name, frames in self._clip_frames.items():
            for t, v in frames:
                if t is not None:
                    self._get_cached_variant(t, v)
        for layer_id, cells in self._clip_cells.items():
            layer = self.tile_layers.get(layer_id)
            if layer is None:
                continue
            for x, y in cells:
                tile = layer.tiles.get((x, y))
                if tile is None or not isinstance(tile.ttype, int):
                    continue
                flags = _tile_flip_flags(tile)
                if not flags:
                    continue
                for t, v in self._clip_frames.get(cells[(x, y)], ()):
                    if t is not None:
                        self._get_cached_variant(t, v, flags)
        self.data = None

    def _clip_frame_surface(
        self, name: str, x: int, y: int, ttype: int, flip_flags: int, time_ms: int
    ) -> Surface | None:
        clip = self._clips[name]
        n = len(clip.frames)
        phase = 0
        if clip.mode == "random_start_times":
            phase = ((x * 73856093) ^ (y * 19349663) ^ (ttype * 83492791)) % n
        idx = _frame_index_at(clip, time_ms, phase)
        t, v = self._clip_frames[name][idx]
        if t is None:
            return None
        return self._get_cached_variant(t, v, flip_flags)

    def _cell_surface(
        self,
        layer_id: int,
        x: int,
        y: int,
        tile,
        time_ms: int,
    ) -> Surface | None:
        clip_name = self._clip_cells.get(layer_id, {}).get((x, y))
        if clip_name is not None:
            surf = self._clip_frame_surface(clip_name, x, y, tile.ttype, _tile_flip_flags(tile), time_ms)
            if surf is not None:
                return surf
            return self._get_cached_variant(tile.ttype, tile.variant, _tile_flip_flags(tile))
        display_variant = self._compute_display_variant(
            tile.variant,
            tile.ttype,
            x,
            y,
            time_ms,
            stride_off=(layer_id, x, y) in self._stride_off,
        )
        return self._get_cached_variant(
            tile.ttype,
            display_variant,
            _tile_flip_flags(tile),
        )

    def _compute_display_variant(
        self,
        variant: int,
        ttype: int,
        x: int,
        y: int,
        time_ms: int,
        stride_off: bool = False,
    ) -> int:
        anim = self._tileset_animations.get(ttype)
        if anim is None or stride_off:
            return variant

        frame_count = anim["frame_count"]
        frame_idx = (time_ms // anim["frame_duration_ms"]) % frame_count

        if anim.get("animation_mode") == "random_start_times":
            phase = ((x * 73856093) ^ (y * 19349663) ^ (ttype * 83492791)) % frame_count
            frame_idx = (frame_idx + phase) % frame_count

        return variant + frame_idx * anim["frame_stride"]

    def render(
        self,
        target: Surface,
        camera_xy: tuple[float, float] | tuple[int, int] = (0, 0),
        viewport_size: tuple[int, int] | None = None,
        *,
        current_time_ms: float | None = None,
    ) -> LayerRenderStats:
        """Render visible tile layers.

        Tile-only by design: object layers are never drawn here. Blit
        object surfaces (e.g. from ``TilemapData.get_object_surfaces``)
        yourself after rendering, in your own order with your own
        viewport culling.

        Tiles are blitted per layer in natural chunk order.  When
        ``layer.y_sort`` is enabled, tiles within each chunk are sorted by
        their tile-space Y coordinate before blitting.
        """
        cam_x, cam_y = float(camera_xy[0]), float(camera_xy[1])
        if viewport_size is None:
            viewport = target.get_rect()
        else:
            viewport = Rect(0, 0, viewport_size[0], viewport_size[1])

        min_x = int(cam_x // self._eff_w) - 1
        max_x = int((cam_x + viewport.width) // self._eff_w) + 1
        min_y = int(cam_y // self._eff_h) - 1
        max_y = int((cam_y + viewport.height) // self._eff_h) + 1

        if current_time_ms is None:
            current_time_ms = pygame.time.get_ticks()
        time_ms = int(current_time_ms)

        drawn = 0
        skipped = 0
        visible_layers = 0

        min_cx = min_x // CHUNK_SIZE
        max_cx = max_x // CHUNK_SIZE
        min_cy = min_y // CHUNK_SIZE
        max_cy = max_y // CHUNK_SIZE

        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            if not layer.visible:
                continue
            visible_layers += 1

            chunks = self._layer_chunks[layer_id]

            for cx in range(min_cx, max_cx + 1):
                for cy in range(min_cy, max_cy + 1):
                    chunk = chunks.get((cx, cy))
                    if not chunk:
                        continue

                    tile_iter = chunk
                    if layer.y_sort:
                        origin = layer.y_sort_origin
                        tile_iter = sorted(chunk, key=lambda p: p[1] * self._eff_h + origin)

                    for x, y in tile_iter:
                        if not (min_x <= x <= max_x and min_y <= y <= max_y):
                            continue
                        tile = layer.tiles[(x, y)]
                        cell = self._cell_surface(layer_id, x, y, tile, time_ms)
                        if cell is None:
                            skipped += 1
                            continue

                        target.blit(
                            cell,
                            (x * self._eff_w - cam_x, y * self._eff_h - cam_y),
                        )
                        drawn += 1

        return LayerRenderStats(drawn_tiles=drawn, skipped_tiles=skipped, visible_layers=visible_layers)

    @property
    def sorted_layer_ids(self) -> list[int]:
        return list(self._sorted_layer_ids)
