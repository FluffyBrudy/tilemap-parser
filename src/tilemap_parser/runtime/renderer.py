from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import pygame
from pygame import Rect, Surface, transform

from .map_loader import TilemapData


@dataclass(frozen=True)
class LayerRenderStats:
    drawn_tiles: int
    skipped_tiles: int
    visible_layers: int


class TileLayerRenderer:
    def __init__(
        self, data: TilemapData, *, include_hidden_layers: bool = False
    ) -> None:
        self.data = data
        self.tile_layers = data.get_tile_layers_dict(
            include_hidden=include_hidden_layers
        )
        self._sorted_layer_ids = sorted(
            self.tile_layers.keys(),
            key=lambda lid: (self.tile_layers[lid].z_index, lid),
        )
        self._variant_cache: Dict[Tuple[int, int], Optional[Surface]] = {}
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

        self._tileset_animations: Dict[int, dict] = {}
        for ts_idx, ts in enumerate(data.parsed.tilesets):
            if ts.animation is not None:
                self._tileset_animations[ts_idx] = {
                    "frame_count": ts.animation.frame_count,
                    "frame_duration_ms": ts.animation.frame_duration_ms,
                    "frame_stride": ts.animation.frame_stride,
                    "loop": ts.animation.loop,
                    "animation_mode": ts.animation.animation_mode,
                }

    def get_layer_dict(self) -> Dict[int, object]:
        return dict(self.tile_layers)

    def _get_cached_variant(self, ttype: int, variant: int) -> Optional[Surface]:
        key = (ttype, variant)
        if key not in self._variant_cache:
            cell = self.data.get_tile_surface(
                ttype, variant, copy_surface=True
            )
            if cell is not None and self._rs != 1.0:
                cell = transform.scale(cell, (self._eff_w, self._eff_h))
            self._variant_cache[key] = cell
        return self._variant_cache[key]

    def warm_cache(self) -> None:
        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            for tile in layer.tiles.values():
                if isinstance(tile.ttype, int):
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
        stride = anim["frame_stride"]
        frame_count = anim["frame_count"]
        frame_idx = int(time_ms / anim["frame_duration_ms"]) % frame_count
        if anim.get("animation_mode") == "random_start_times":
            phase = hash((x, y, ttype)) % frame_count
            frame_idx = (frame_idx + phase) % frame_count
        return variant + frame_idx * stride

    def render(
        self,
        target: Surface,
        camera_xy: Union[Tuple[float, float], Tuple[int, int]] = (0, 0),
        viewport_size: Optional[Tuple[int, int]] = None,
        *,
        current_time_ms: Optional[float] = None,
    ) -> LayerRenderStats:
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

        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            if not layer.visible:
                continue
            visible_layers += 1
            for (x, y), tile in layer.tiles.items():
                if x < min_x or x > max_x or y < min_y or y > max_y:
                    skipped += 1
                    continue
                if not isinstance(tile.ttype, int):
                    skipped += 1
                    continue
                display_variant = self._compute_display_variant(
                    tile.variant, tile.ttype, x, y, time_ms
                )
                cell = self._get_cached_variant(tile.ttype, display_variant)
                if cell is None:
                    skipped += 1
                    continue
                target.blit(cell, (x * self._eff_w - cam_x, y * self._eff_h - cam_y))
                drawn += 1

        return LayerRenderStats(
            drawn_tiles=drawn, skipped_tiles=skipped, visible_layers=visible_layers
        )
