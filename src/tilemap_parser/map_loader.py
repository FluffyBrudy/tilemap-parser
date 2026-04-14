from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pygame
from pygame import Rect, Surface

from .map_parse import MapParseError, ParsedLayer, ParsedMap, ParsedTile, parse_map_file

PathLike = Union[str, Path]


class TilemapData:
    def __init__(
        self,
        parsed: ParsedMap,
        surfaces: List[Optional[Surface]],
        resolved_paths: List[Path],
        warnings: List[str],
        *,
        map_path: Optional[Path] = None,
    ) -> None:
        self.parsed = parsed
        self.surfaces = surfaces
        self.resolved_paths = resolved_paths
        self.warnings = warnings
        self.map_path = map_path
        self._tw, self._th = parsed.meta.tile_size
        self._build_path_index()
        self._normalize_tile_ttypes()

    @classmethod
    def load(
        cls,
        path: PathLike,
        *,
        extra_search_base: Optional[Path] = None,
        skip_missing_images: bool = True,
    ) -> "TilemapData":
        p = Path(path)
        parsed = parse_map_file(p)
        map_dir = p.parent

        surfaces: List[Optional[Surface]] = []
        resolved_paths: List[Path] = []
        warnings: List[str] = []

        if not pygame.get_init():
            pygame.init()

        for i, ts in enumerate(parsed.tilesets):
            resolved = _resolve_resource_path(ts.path, map_dir, extra_search_base)
            resolved_paths.append(resolved)
            if not resolved.is_file():
                warnings.append(f"Tileset missing ({i}): {ts.path!r} -> {resolved}")
                surfaces.append(None)
                continue
            try:
                surfaces.append(pygame.image.load(str(resolved)).convert_alpha())
            except pygame.error as e:
                msg = f"Tileset load failed ({i}) {resolved}: {e}"
                warnings.append(msg)
                if not skip_missing_images:
                    raise MapParseError(msg) from e
                surfaces.append(None)

        return cls(parsed, surfaces, resolved_paths, warnings, map_path=p)

    def _build_path_index(self) -> None:
        self._path_to_index: Dict[str, int] = {}
        for i, ts in enumerate(self.parsed.tilesets):
            raw = ts.path.replace("\\", "/")
            rp = self.resolved_paths[i]
            self._path_to_index[raw] = i
            self._path_to_index[str(rp)] = i
            self._path_to_index[str(rp.resolve())] = i
            self._path_to_index[Path(raw).name] = i

    def _lookup_tileset_index(self, ref: str) -> int:
        norm = ref.replace("\\", "/")
        if norm in self._path_to_index:
            return self._path_to_index[norm]
        pref = Path(ref)
        for i, rp in enumerate(self.resolved_paths):
            try:
                if rp.resolve() == pref.resolve():
                    return i
            except (OSError, ValueError):
                pass
            if rp.name == pref.name:
                return i
        return -1

    def _normalize_tile_ttypes(self) -> None:
        for layer in self.parsed.layers:
            if layer.layer_type == "object":
                continue
            for pos, tile in layer.tiles.items():
                if isinstance(tile.ttype, str):
                    idx = self._lookup_tileset_index(tile.ttype)
                    if idx < 0:
                        self.warnings.append(
                            f"Unresolved tileset ref {tile.ttype!r} at layer {layer.name!r} cell {pos}"
                        )
                    tile.ttype = idx

    @property
    def tile_size(self) -> Tuple[int, int]:
        return self.parsed.meta.tile_size

    @property
    def map_size(self) -> Tuple[int, int]:
        return self.parsed.meta.map_size

    def get_raw(self) -> dict:
        return deepcopy(self.parsed.raw)

    def get_layers(
        self,
        *,
        include_hidden: bool = True,
        layer_type: Optional[str] = None,
        sort_by_zindex: bool = True,
    ) -> List[ParsedLayer]:
        layers = self.parsed.layers
        if layer_type is not None:
            layers = [layer for layer in layers if layer.layer_type == layer_type]
        if not include_hidden:
            layers = [layer for layer in layers if layer.visible]
        if sort_by_zindex:
            layers = sorted(layers, key=lambda layer: (layer.z_index, layer.id))
        return list(layers)

    def get_layer(self, layer_id_or_name: Union[int, str]) -> Optional[ParsedLayer]:
        if isinstance(layer_id_or_name, int):
            for layer in self.parsed.layers:
                if layer.id == layer_id_or_name:
                    return layer
            return None
        for layer in self.parsed.layers:
            if layer.name == layer_id_or_name:
                return layer
        return None

    def get_tile_layers_dict(self, *, include_hidden: bool = True) -> Dict[int, ParsedLayer]:
        return {layer.id: layer for layer in self.get_layers(include_hidden=include_hidden, layer_type="tile", sort_by_zindex=False)}

    def get_image(self, variant: int, ttype: int = 0, *, copy_surface: bool = True) -> Optional[Surface]:
        if ttype < 0 or ttype >= len(self.surfaces):
            return None
        source = self.surfaces[ttype]
        if source is None:
            return None
        return _variant_surface(source, variant, self.tile_size, copy_surface=copy_surface)

    def get_tile_surface(self, ttype: int, variant: int, *, copy_surface: bool = True) -> Optional[Surface]:
        return self.get_image(variant=variant, ttype=ttype, copy_surface=copy_surface)

    def get_tile_at(self, layer_id_or_name: Union[int, str], x: int, y: int) -> Optional[ParsedTile]:
        layer = self.get_layer(layer_id_or_name)
        if layer is None:
            return None
        return layer.tiles.get((x, y))

    def get_tile_surface_at(self, layer_id_or_name: Union[int, str], x: int, y: int) -> Optional[Surface]:
        tile = self.get_tile_at(layer_id_or_name, x, y)
        if tile is None or not isinstance(tile.ttype, int):
            return None
        return self.get_tile_surface(tile.ttype, tile.variant)


def _variant_surface(
    surf: Surface,
    variant: int,
    tile_size: Tuple[int, int],
    *,
    copy_surface: bool,
) -> Optional[Surface]:
    tw, th = tile_size
    if tw <= 0 or th <= 0:
        return None
    cols = max(1, surf.get_width() // tw)
    col = variant % cols
    row = variant // cols
    src = Rect(col * tw, row * th, tw, th)
    if not surf.get_rect().contains(src):
        return None
    cell = surf.subsurface(src)
    return cell.copy() if copy_surface else cell


def _resolve_resource_path(path_str: str, map_dir: Path, extra_search_base: Optional[Path]) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    candidate = (map_dir / path).resolve()
    if candidate.is_file():
        return candidate
    if extra_search_base is not None:
        extra_candidate = (Path(extra_search_base) / path_str).resolve()
        if extra_candidate.is_file():
            return extra_candidate
    return candidate


def load_map(path: PathLike, *, extra_search_base: Optional[Path] = None, skip_missing_images: bool = True) -> TilemapData:
    return TilemapData.load(path, extra_search_base=extra_search_base, skip_missing_images=skip_missing_images)
