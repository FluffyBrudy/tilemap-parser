from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

from pygame import Rect, Surface

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

    def get_layer_dict(self) -> Dict[int, object]:
        return dict(self.tile_layers)

    def _get_cached_variant(self, ttype: int, variant: int) -> Optional[Surface]:
        key = (ttype, variant)
        if key not in self._variant_cache:
            self._variant_cache[key] = self.data.get_tile_surface(
                ttype, variant, copy_surface=True
            )
        return self._variant_cache[key]

    def warm_cache(self) -> None:
        for layer_id in self._sorted_layer_ids:
            layer = self.tile_layers[layer_id]
            for tile in layer.tiles.values():
                if isinstance(tile.ttype, int):
                    self._get_cached_variant(tile.ttype, tile.variant)
        self.data = None

    def render(
        self,
        target: Surface,
        camera_xy: Union[Tuple[float, float], Tuple[int, int]] = (0, 0),
        viewport_size: Optional[Tuple[int, int]] = None,
    ) -> LayerRenderStats:
        cam_x, cam_y = float(camera_xy[0]), float(camera_xy[1])
        if viewport_size is None:
            viewport = target.get_rect()
        else:
            viewport = Rect(0, 0, viewport_size[0], viewport_size[1])

        min_x = int(cam_x // self._tile_w) - 1
        max_x = int((cam_x + viewport.width) // self._tile_w) + 1
        min_y = int(cam_y // self._tile_h) - 1
        max_y = int((cam_y + viewport.height) // self._tile_h) + 1

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
                cell = self._get_cached_variant(tile.ttype, tile.variant)
                if cell is None:
                    skipped += 1
                    continue
                target.blit(cell, (x * self._tile_w - cam_x, y * self._tile_h - cam_y))
                drawn += 1

        return LayerRenderStats(
            drawn_tiles=drawn, skipped_tiles=skipped, visible_layers=visible_layers
        )
