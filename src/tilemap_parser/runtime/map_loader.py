from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union

import pygame
from pygame import Rect, Surface

from ..parser.map_parse import (
    MapParseError,
    ObjectAnimation,
    ParsedLayer,
    ParsedMap,
    ParsedObject,
    ParsedTile,
    parse_map_file,
)
from ..parser.node_parse import parse_nodes_dict
from .area_node import AreaNode
from .particles import ParticleEmitterNode

PathLike = Union[str, Path]


class BackgroundLayer:
    __slots__ = ("image_path", "image_rect", "surface")

    def __init__(
        self,
        image_path: str,
        image_rect: tuple[int, int, int, int] | None,
        surface: Surface | None,
    ) -> None:
        self.image_path = image_path
        self.image_rect = image_rect
        self.surface = surface


# Public return for get_object_animation (exposed, not internal ObjectAnimation)
class AnimData(TypedDict, total=True):
    frames: List[Surface]
    properties: Dict[str, object]
    frame_duration_ms: float
    loop: bool
    animation_mode: Literal["default", "random_start_times"]
    frame_w: int
    frame_h: int


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
        # Pixel/world offset applied while normalizing negative source coordinates.
        self.origin_offset = (0, 0)
        self.area_nodes: List[AreaNode] = []
        self.particle_emitters: List[ParticleEmitterNode] = []
        self.background_layer: Optional[BackgroundLayer] = None
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
        nodes_dir: Optional[PathLike] = None,
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
                surf = pygame.image.load(str(resolved))
                try:
                    surf = surf.convert_alpha()
                except pygame.error:
                    pass
                surfaces.append(surf)
            except pygame.error as e:
                msg = f"Tileset load failed ({i}) {resolved}: {e}"
                warnings.append(msg)
                if not skip_missing_images:
                    raise MapParseError(msg) from e
                surfaces.append(None)

        nodes_name = f"{p.stem}.nodes.json"
        nodes_candidates: List[Path] = []
        if nodes_dir is not None:
            nodes_candidates.append(Path(nodes_dir) / nodes_name)
        else:
            nodes_candidates = [
                map_dir / nodes_name,
                map_dir.parent / "nodes" / nodes_name,
            ]
            if extra_search_base is not None:
                nodes_candidates.append(extra_search_base / "nodes" / nodes_name)
        for nodes_path in nodes_candidates:
            if nodes_path.is_file():
                try:
                    nodes_text = nodes_path.read_text(encoding="utf-8")
                    nodes_raw = json.loads(nodes_text)
                    parsed.nodes = parse_nodes_dict(nodes_raw)
                    groups_raw = nodes_raw.get("groups", [])
                    if not isinstance(groups_raw, list):
                        raise MapParseError("root.groups must be a list")
                    parsed.node_groups = groups_raw
                except (json.JSONDecodeError, OSError, MapParseError) as e:
                    warnings.append(f"Failed to load nodes: {e}")
                break

        origin_offset = _normalize_origin(parsed)
        result = cls(parsed, surfaces, resolved_paths, warnings, map_path=p)
        result.origin_offset = origin_offset
        result.area_nodes = [
            AreaNode(n, render_scale=result.render_scale)
            for n in parsed.nodes
            if n.node_type == "area"
        ]
        result.particle_emitters = [
            ParticleEmitterNode(n) for n in parsed.nodes if n.node_type == "particle_emitter"
        ]

        for layer in parsed.layers:
            if layer.image_path is not None and layer.layer_type == "image":
                bg_path = _resolve_resource_path(layer.image_path, map_dir, extra_search_base)
                bg_surface: Optional[Surface] = None
                if bg_path.is_file():
                    try:
                        bg_surface = pygame.image.load(str(bg_path))
                        try:
                            bg_surface = bg_surface.convert_alpha()
                        except pygame.error:
                            pass
                    except pygame.error as e:
                        msg = f"Background layer image load failed: {e}"
                        warnings.append(msg)
                        if not skip_missing_images:
                            raise MapParseError(msg) from e
                else:
                    msg = f"Background layer image not found: {layer.image_path!r} -> {bg_path}"
                    warnings.append(msg)
                    if not skip_missing_images:
                        raise MapParseError(msg)
                result.background_layer = BackgroundLayer(
                    image_path=layer.image_path,
                    image_rect=layer.image_rect,
                    surface=bg_surface,
                )
                break

        return result

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
                        continue
                    tile.ttype = idx

    @property
    def tile_size(self) -> Tuple[int, int]:
        return self.parsed.meta.tile_size

    @property
    def map_size(self) -> Tuple[int, int]:
        return self.parsed.meta.map_size

    @property
    def render_scale(self) -> float:
        return self.parsed.meta.render_scale

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

    def build_tile_map(
        self,
        exclude_layers: Optional[set[str]] = None,
        use_gids: bool = False,
    ) -> Dict[Tuple[int, int], int]:
        """Build a ``{(col, row): tile_id}`` dict for use with
        :class:`tilemap_parser.runtime.movement.CollisionRunner`.

        Only tile layers are scanned; object layers are skipped
        automatically.  Pass *exclude_layers* to skip specific tile
        layers by name (e.g. collisions, overlays).

        When *use_gids* is ``True``, the returned values are global tile
        IDs (firstgid + variant) so that tiles from different tilesets
        with the same variant number produce distinct values.
        """
        tile_map: Dict[Tuple[int, int], int] = {}
        for layer in self.parsed.layers:
            if layer.layer_type != "tile":
                continue
            if exclude_layers and layer.name in exclude_layers:
                continue
            for (tx, ty), tile in layer.tiles.items():
                if not isinstance(tile.ttype, int):
                    continue
                if use_gids:
                    if tile.gid is not None:
                        tile_map[(tx, ty)] = tile.gid
                    else:
                        ts_idx = tile.ttype
                        if 0 <= ts_idx < len(self.parsed.tilesets):
                            ts = self.parsed.tilesets[ts_idx]
                            if ts.firstgid:
                                tile_map[(tx, ty)] = ts.firstgid + tile.variant
                            else:
                                tile_map[(tx, ty)] = tile.variant
                        else:
                            tile_map[(tx, ty)] = tile.variant
                else:
                    tile_map[(tx, ty)] = tile.variant
        return tile_map

    def get_image(self, variant: int, ttype: int = 0, *, copy_surface: bool = True) -> Optional[Surface]:
        if ttype < 0 or ttype >= len(self.surfaces):
            return None
        source = self.surfaces[ttype]
        if source is None:
            return None
        return _variant_surface(source, variant, self.tile_size, copy_surface=copy_surface)

    def get_object_surface(self, obj: ParsedObject, *, copy_surface: bool = True) -> Optional[Surface]:
        if obj.ttype < 0 or obj.ttype >= len(self.surfaces):
            return None
        source = self.surfaces[obj.ttype]
        if source is None:
            return None
        if (obj.area.w, obj.area.h) == (source.get_width(), source.get_height()):
            return source.copy() if copy_surface else source
        return _variant_surface(source, obj.variant, self.tile_size, copy_surface=copy_surface)

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

    def get_object_surface_by_id(
        self, layer_id_or_name: Union[int, str], object_id: int, *, copy_surface: bool = True, scaled: bool = False
    ) -> Optional[Tuple[Surface, float, float]]:
        layer = self.get_layer(layer_id_or_name)
        if layer is None or layer.layer_type != "object":
            return None
        obj = layer.objects.get(object_id)
        if obj is None:
            return None
        surf = self.get_object_surface(obj, copy_surface=copy_surface)
        if surf is None:
            return None
        rs = self.render_scale if scaled else 1.0
        x = obj.area.x * rs
        y = obj.area.y * rs
        if scaled and rs != 1.0:
            w, h = surf.get_size()
            surf = pygame.transform.scale(surf, (int(w * rs), int(h * rs)))
        return surf, x, y

    def get_object_surfaces(
        self, layer_id_or_name: Union[int, str], *, copy_surface: bool = True, scaled: bool = False
    ) -> List[Tuple[Surface, float, float, int]]:
        layer = self.get_layer(layer_id_or_name)
        if layer is None or layer.layer_type != "object":
            return []
        result: List[Tuple[Surface, float, float, int]] = []
        rs = self.render_scale if scaled else 1.0
        for oid, obj in layer.objects.items():
            surf = self.get_object_surface(obj, copy_surface=copy_surface)
            if surf is not None:
                x = obj.area.x * rs
                y = obj.area.y * rs
                if scaled and rs != 1.0:
                    w, h = surf.get_size()
                    surf = pygame.transform.scale(surf, (int(w * rs), int(h * rs)))
                result.append((surf, x, y, oid))
        return result

    def get_tileset_animation(self, ttype: int) -> Optional[dict]:
        if 0 <= ttype < len(self.parsed.tilesets):
            anim = self.parsed.tilesets[ttype].animation
            if anim is not None:
                return {
                    "frame_count": anim.frame_count,
                    "frame_duration_ms": anim.frame_duration_ms,
                    "frame_stride": anim.frame_stride,
                    "loop": anim.loop,
                    "animation_mode": anim.animation_mode,
                    "frame_w": anim.frame_w,
                    "frame_h": anim.frame_h,
                }
        return None

    def get_object_animation(self, obj: ParsedObject, render_scale: float = 1.0) -> Optional[AnimData]:
        """Return effective object animation as ``AnimData`` or ``None``.

        When per-object ``animation`` is ``None``, falls back to the object's
        tileset ``ParsedTileset.animation`` (shared strip). ``render_scale``
        scales both ``frames`` and ``frame_w/h`` in the returned dict
        (default ``1.0`` leaves at source resolution). No ``Surface`` overload -
        single dict with ``frames`` + ``properties`` + ``loop``/``duration``/``mode``/``w/h``.
        """
        if not isinstance(render_scale, (int, float)) or not math.isfinite(render_scale) or render_scale <= 0:
            raise ValueError(f"render_scale must be finite and > 0, got {render_scale!r}")
        # effective animation (per-object or tileset fallback) - internal ObjectAnimationData
        anim_data: Optional[ObjectAnimation] = obj.animation  # internal, keep frame_count
        if anim_data is None:
            t_anim = self.get_tileset_animation(obj.ttype)
            if t_anim is None:
                return None
            anim_data = ObjectAnimation(
                frame_count=t_anim["frame_count"],
                frame_duration_ms=t_anim["frame_duration_ms"],
                loop=t_anim.get("loop", True),
                animation_mode=t_anim.get("animation_mode", "default"),
                frames=[],
                frame_stride=t_anim.get("frame_stride", 1),
                frame_w=t_anim.get("frame_w"),
                frame_h=t_anim.get("frame_h"),
            )
        if obj.ttype < 0 or obj.ttype >= len(self.surfaces):
            return None
        source = self.surfaces[obj.ttype]
        if source is None:
            return None
        # frame dimensions - prefer animation's w/h, else area, else tile_size, scaled by render_scale
        fw = getattr(anim_data, "frame_w", None)
        if fw is None:
            fw = obj.area.w if obj.area.w > 0 else self._tw
        fh = getattr(anim_data, "frame_h", None)
        if fh is None:
            fh = obj.area.h if obj.area.h > 0 else self._th
        if fw <= 0 or fh <= 0:
            return None
        # apply render_scale to dimensions
        if render_scale != 1.0:
            fw = int(fw * render_scale)
            fh = int(fh * render_scale)
        # cols based on original fw before scale for correct slicing
        orig_fw = getattr(anim_data, "frame_w", None)
        if orig_fw is None:
            orig_fw = obj.area.w if obj.area.w > 0 else self._tw
        if orig_fw is None or orig_fw <= 0:
            orig_fw = fw
        cols = max(1, source.get_width() // orig_fw) if render_scale != 1.0 else max(1, source.get_width() // fw)
        if anim_data.frames:
            frame_indices = anim_data.frames
        else:
            stride = getattr(anim_data, "frame_stride", 1)
            if stride is None or stride <= 0:
                stride = 1
            if stride == 1:
                frame_indices = list(range(anim_data.frame_count))
            else:
                frame_indices = [i * stride for i in range(anim_data.frame_count)]
        frames: List[Surface] = []
        for fi in frame_indices:
            col = fi % cols
            row = fi // cols
            src_fw = getattr(anim_data, "frame_w", None) or (obj.area.w if obj.area.w > 0 else self._tw)
            src_fh = getattr(anim_data, "frame_h", None) or (obj.area.h if obj.area.h > 0 else self._th)
            src = Rect(col * src_fw, row * src_fh, src_fw, src_fh)
            if not source.get_rect().contains(src):
                surf = Surface((src_fw, src_fh), pygame.SRCALPHA)
            else:
                cell = source.subsurface(src)
                surf = cell.copy()
            if render_scale != 1.0:
                surf = pygame.transform.scale(surf, (fw, fh))
            frames.append(surf)
        return {
            "frames": frames,
            "properties": dict(obj.properties) if obj.properties else {},
            "frame_duration_ms": float(anim_data.frame_duration_ms),
            "loop": bool(anim_data.loop),
            "animation_mode": str(anim_data.animation_mode),
            "frame_w": fw,
            "frame_h": fh,
        }


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


def _normalize_origin(parsed: ParsedMap) -> Tuple[int, int]:
    tw, th = parsed.meta.tile_size
    rs = parsed.meta.render_scale
    eff_w = int(tw * rs)
    eff_h = int(th * rs)
    if eff_w <= 0 or eff_h <= 0:
        return (0, 0)

    min_x = 0
    min_y = 0
    max_x = parsed.meta.map_size[0]
    max_y = parsed.meta.map_size[1]

    for layer in parsed.layers:
        for x, y in layer.tiles.keys():
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + 1)
            max_y = max(max_y, y + 1)

        for obj in layer.objects.values():
            left = math.floor(obj.area.x / eff_w)
            top = math.floor(obj.area.y / eff_h)
            right = math.ceil((obj.area.x + obj.area.w) / eff_w)
            bottom = math.ceil((obj.area.y + obj.area.h) / eff_h)
            min_x = min(min_x, left)
            min_y = min(min_y, top)
            max_x = max(max_x, right)
            max_y = max(max_y, bottom)

    for node in parsed.nodes:
        left = math.floor(node.area.x / eff_w)
        top = math.floor(node.area.y / eff_h)
        right = math.ceil((node.area.x + node.area.w) / eff_w)
        bottom = math.ceil((node.area.y + node.area.h) / eff_h)
        min_x = min(min_x, left)
        min_y = min(min_y, top)
        max_x = max(max_x, right)
        max_y = max(max_y, bottom)

    if min_x >= 0 and min_y >= 0:
        parsed.meta.map_size = (max_x, max_y)
        return (0, 0)

    shift_x = -min_x
    shift_y = -min_y
    pixel_shift_x = shift_x * eff_w
    pixel_shift_y = shift_y * eff_h

    for layer in parsed.layers:
        if layer.tiles:
            shifted_tiles = {}
            for (x, y), tile in layer.tiles.items():
                new_pos = (x + shift_x, y + shift_y)
                tile.pos = new_pos
                shifted_tiles[new_pos] = tile
            layer.tiles = shifted_tiles

        for obj in layer.objects.values():
            obj.area.x += pixel_shift_x
            obj.area.y += pixel_shift_y

    for node in parsed.nodes:
        node.area.x += pixel_shift_x
        node.area.y += pixel_shift_y

    parsed.meta.map_size = (max_x + shift_x, max_y + shift_y)
    parsed.meta.initial_map_size = (
        parsed.meta.initial_map_size[0] + shift_x,
        parsed.meta.initial_map_size[1] + shift_y,
    )
    parsed.meta.scroll = (
        parsed.meta.scroll[0] + pixel_shift_x,
        parsed.meta.scroll[1] + pixel_shift_y,
    )
    return (pixel_shift_x, pixel_shift_y)


def load_map(path: PathLike, *, extra_search_base: Optional[Path] = None, skip_missing_images: bool = True, nodes_dir: Optional[PathLike] = None) -> TilemapData:
    return TilemapData.load(path, extra_search_base=extra_search_base, skip_missing_images=skip_missing_images, nodes_dir=nodes_dir)
