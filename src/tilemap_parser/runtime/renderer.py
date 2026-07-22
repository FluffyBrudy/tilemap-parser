from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pygame
from pygame import Rect, Surface, transform

from .map_loader import TilemapData
from .protocols import ExtraObject

CHUNK_SIZE = 32


@dataclass(frozen=True)
class LayerRenderStats:
    drawn_tiles: int
    skipped_tiles: int
    visible_layers: int


class TileLayerRenderer:
    def __init__(self, data: TilemapData, *, include_hidden_layers: bool = False) -> None:
        self.data = data
        self.tile_layers = data.get_tile_layers_dict(include_hidden=include_hidden_layers)
        self._sorted_layer_ids = sorted(
            self.tile_layers.keys(),
            key=lambda lid: (self.tile_layers[lid].z_index, lid),
        )

        self._variant_cache: dict[tuple[int, int], Surface | None] = {}

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

    def get_layer_dict(self) -> dict[int, object]:
        return dict(self.tile_layers)

    def _get_cached_variant(self, ttype: int, variant: int) -> Surface | None:
        key = (ttype, variant)
        if key not in self._variant_cache:
            cell = self.data.get_tile_surface(ttype, variant, copy_surface=True)
            if cell is not None and self._rs != 1.0:
                cell = transform.scale(cell, (self._eff_w, self._eff_h))
            self._variant_cache[key] = cell
        return self._variant_cache[key]

    def warm_cache(self) -> None:
        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            for tile in layer.tiles.values():
                if not isinstance(tile.ttype, int):
                    continue
                anim = self._tileset_animations.get(tile.ttype)
                if anim is not None:
                    frame_count = anim["frame_count"]
                    stride = anim["frame_stride"]
                    for f in range(frame_count):
                        self._get_cached_variant(tile.ttype, tile.variant + f * stride)
                else:
                    self._get_cached_variant(tile.ttype, tile.variant)
        self.data = None

    def _compute_display_variant(
        self,
        variant: int,
        ttype: int,
        x: int,
        y: int,
        time_ms: int,
    ) -> int:
        anim = self._tileset_animations.get(ttype)
        if anim is None:
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
        extra_objects: Sequence[ExtraObject] | None = None,
        current_time_ms: float | None = None,
    ) -> LayerRenderStats:
        """Render visible tile layers, optionally merged with extra objects.

        When *extra_objects* is provided, each item must have ``surface``,
        ``x``, and ``y`` attributes (duck-typed). Extras are blitted after
        all tile layers, preserving caller order.

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
                        tile = layer.tiles[(x, y)]
                        display_variant = self._compute_display_variant(tile.variant, tile.ttype, x, y, time_ms)
                        cell = self._get_cached_variant(tile.ttype, display_variant)
                        if cell is None:
                            skipped += 1
                            continue

                        target.blit(
                            cell,
                            (x * self._eff_w - cam_x, y * self._eff_h - cam_y),
                        )
                        drawn += 1

        if extra_objects:
            for obj in extra_objects:
                surf = obj.surface
                if surf is None:
                    continue
                target.blit(surf, (obj.x - cam_x, obj.y - cam_y))

        return LayerRenderStats(drawn_tiles=drawn, skipped_tiles=skipped, visible_layers=visible_layers)

    @property
    def sorted_layer_ids(self) -> list[int]:
        return list(self._sorted_layer_ids)
