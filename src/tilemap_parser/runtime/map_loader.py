from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Literal, TypedDict

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

PathLike = str | Path


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


class AnimData(TypedDict, total=True):
    frames: list[Surface]
    properties: dict[str, object]
    frame_duration_ms: float
    loop: bool
    animation_mode: Literal["default", "random_start_times"]
    frame_w: int
    frame_h: int


class TilemapData:
    def __init__(
        self,
        parsed: ParsedMap,
        surfaces: list[Surface | None],
        resolved_paths: list[Path],
        warnings: list[str],
        *,
        map_path: Path | None = None,
        map_dir: Path | None = None,
        extra_search_base: Path | None = None,
        skip_missing_images: bool = True,
        tile_offset: tuple[int, int] = (0, 0),
    ) -> None:
        self.parsed = parsed
        self.surfaces = surfaces
        self.resolved_paths = resolved_paths
        self.warnings = warnings
        self.map_path = map_path

        if map_dir is not None:
            self._map_dir = Path(map_dir)
        elif map_path is not None:
            self._map_dir = Path(map_path).parent
        else:
            self._map_dir = Path(".")
        self._extra_search_base = Path(extra_search_base) if extra_search_base is not None else None
        self._skip_missing_images = skip_missing_images
        self._bg_cache: dict[str, Surface | None] = {}
        self.tile_offset = (tile_offset[0], tile_offset[1])
        self.origin_offset = (0, 0)
        self.area_nodes: list[AreaNode] = []
        self.particle_emitters: list[ParticleEmitterNode] = []
        self.background_layer: BackgroundLayer | None = None
        self._tw, self._th = parsed.meta.tile_size
        self._build_path_index()
        self._normalize_tile_ttypes()

    @classmethod
    def load(
        cls,
        path: PathLike,
        *,
        extra_search_base: Path | None = None,
        skip_missing_images: bool = True,
        nodes_dir: PathLike | None = None,
        offset_tiles: tuple[int, int] | None = None,
        offset_x: int | None = None,
        offset_y: int | None = None,
    ) -> "TilemapData":
        p = Path(path)
        parsed = parse_map_file(p)
        map_dir = p.parent

        surfaces: list[Surface | None] = []
        resolved_paths: list[Path] = []
        warnings: list[str] = []

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
        nodes_candidates: list[Path] = []
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
        ox, oy = _resolve_tile_offset(offset_tiles, offset_x, offset_y)
        if ox or oy:
            user_px = _apply_tile_offset(parsed, ox, oy)
            origin_offset = (origin_offset[0] + user_px[0], origin_offset[1] + user_px[1])
        result = cls(
            parsed,
            surfaces,
            resolved_paths,
            warnings,
            map_path=p,
            map_dir=map_dir,
            extra_search_base=extra_search_base,
            skip_missing_images=skip_missing_images,
            tile_offset=(ox, oy),
        )
        result.origin_offset = origin_offset
        result.area_nodes = [
            AreaNode(n, render_scale=result.render_scale) for n in parsed.nodes if n.node_type == "area"
        ]
        result.particle_emitters = [ParticleEmitterNode(n) for n in parsed.nodes if n.node_type == "particle_emitter"]

        for layer in parsed.layers:
            if layer.image_path is not None and layer.layer_type == "image" and layer.visible:
                bg_surface = result._load_background_surface(layer.image_path)
                result.background_layer = BackgroundLayer(
                    image_path=layer.image_path,
                    image_rect=layer.image_rect,
                    surface=bg_surface,
                )
                break

        return result

    def resolve_image_path(self, image_path: str) -> Path:
        """Resolve an image-layer ``image_path`` to an absolute path.

        Uses the map directory first (so ``../../assets/x.png`` works),
        falling back to ``extra_search_base`` when given at load time.
        """
        return _resolve_resource_path(image_path, self._map_dir, self._extra_search_base)

    def _load_background_surface(self, image_path: str) -> Surface | None:
        if image_path in self._bg_cache:
            return self._bg_cache[image_path]
        bg_path = self.resolve_image_path(image_path)
        bg_surface: Surface | None = None
        if bg_path.is_file():
            try:
                bg_surface = pygame.image.load(str(bg_path))
                try:
                    bg_surface = bg_surface.convert_alpha()
                except pygame.error:
                    pass
            except pygame.error as e:
                msg = f"Background layer image load failed: {e}"
                self.warnings.append(msg)
                if not self._skip_missing_images:
                    raise MapParseError(msg) from e
        else:
            msg = f"Background layer image not found: {image_path!r} -> {bg_path}"
            self.warnings.append(msg)
            if not self._skip_missing_images:
                raise MapParseError(msg)
        self._bg_cache[image_path] = bg_surface
        return bg_surface

    def _resolve_image_layer(self, layer: ParsedLayer | int | str) -> ParsedLayer | None:
        if isinstance(layer, ParsedLayer):
            return layer
        return self.get_layer(layer)

    def get_image_layer_surface(
        self,
        layer: ParsedLayer | int | str,
        *,
        copy_surface: bool = False,
        include_hidden: bool = False,
    ) -> Surface | None:
        """Load (or return cached) ``Surface`` for an image/bg layer on demand.

        Accepts a ``ParsedLayer``, layer id, or layer name. Returns ``None``
        for unknown layers, layers without ``image_path``, hidden layers
        (unless ``include_hidden=True``), or missing files
        (a warning is recorded; raises ``MapParseError`` when the data was
        loaded with ``skip_missing_images=False``). ``image_rect`` stays
        position metadata — the full image is returned, matching
        ``background_layer.surface``.
        """
        resolved = self._resolve_image_layer(layer)
        if resolved is None or resolved.image_path is None:
            return None
        if not resolved.visible and not include_hidden:
            return None
        surf = self._load_background_surface(resolved.image_path)
        if surf is None:
            return None
        return surf.copy() if copy_surface else surf

    def get_image_layer_surfaces(
        self, *, include_hidden: bool = False, copy_surface: bool = False
    ) -> list[tuple[ParsedLayer, Surface | None]]:
        """Return ``[(layer, surface)]`` for every image layer, loading lazily.

        Hidden layers are skipped unless ``include_hidden=True``.
        Order follows :meth:`get_layers` (z-index sorted). Missing images
        yield ``None`` surfaces (see :meth:`get_image_layer_surface`).
        """
        out: list[tuple[ParsedLayer, Surface | None]] = []
        for lyr in self.get_layers(include_hidden=include_hidden, layer_type="image"):
            out.append(
                (lyr, self.get_image_layer_surface(lyr, copy_surface=copy_surface, include_hidden=include_hidden))
            )
        return out

    def get_placed_image_layer_surface(
        self,
        layer: ParsedLayer | int | str,
        *,
        render_scale: float = 1.0,
        include_hidden: bool = False,
    ) -> Surface | None:
        """Compose one surface from a layer's placements, just as placed.

        The editor records each duplicate copy as an ``(x, y, w, h)`` rect
        (see ``ParsedLayer.image_placements``); this blits every copy —
        base ``image_rect`` first, then placements in paint order — onto a
        single surface sized to their union, scaled by ``render_scale``
        (``1.0`` keeps source pixels). ``stretch`` copies scale to their
        rect; ``repeat`` copies tile floor-plus-remainder within it.

        Returns a fresh surface the caller owns (bake once, reuse), or
        ``None`` for unknown layers, layers without ``image_path``,
        hidden layers (unless ``include_hidden=True``), missing files,
        or layers with no rects at all. Non-positive ``render_scale``
        raises ``ValueError``.
        """
        if not isinstance(render_scale, (int, float)) or not math.isfinite(render_scale) or render_scale <= 0:
            raise ValueError(f"render_scale must be finite and > 0, got {render_scale!r}")
        resolved = self._resolve_image_layer(layer)
        if resolved is None or resolved.image_path is None:
            return None
        if not resolved.visible and not include_hidden:
            return None
        source = self._load_background_surface(resolved.image_path)
        if source is None:
            return None
        rects: list[tuple[int, int, int, int, str]] = []
        if resolved.image_rect is not None:
            x, y, w, h = resolved.image_rect
            rects.append((x, y, w, h, "stretch"))
        for placement in resolved.image_placements:
            rects.append((placement.x, placement.y, placement.w, placement.h, placement.mode))
        rects = [(x, y, w, h, mode) for x, y, w, h, mode in rects if w > 0 and h > 0]
        if not rects:
            return None
        min_x = min(x for x, _, _, _, _ in rects)
        min_y = min(y for _, y, _, _, _ in rects)
        max_x = max(x + w for x, _, w, _, _ in rects)
        max_y = max(y + h for _, y, _, h, _ in rects)
        canvas = Surface(
            (max(1, int(round((max_x - min_x) * render_scale))), max(1, int(round((max_y - min_y) * render_scale)))),
            pygame.SRCALPHA,
        )
        for x, y, w, h, mode in rects:
            dw, dh = max(1, int(round(w * render_scale))), max(1, int(round(h * render_scale)))
            dx, dy = int(round((x - min_x) * render_scale)), int(round((y - min_y) * render_scale))
            if mode == "repeat":
                self._blit_tiled(canvas, source, dx, dy, dw, dh, render_scale)
            else:
                try:
                    tile = pygame.transform.scale(source, (dw, dh))
                except pygame.error:
                    continue
                canvas.blit(tile, (dx, dy))
        return canvas

    @staticmethod
    def _blit_tiled(
        target: Surface,
        source: Surface,
        dx: int,
        dy: int,
        dw: int,
        dh: int,
        render_scale: float,
    ) -> None:
        """Tile ``source`` floor-plus-remainder across a ``dw x dh`` band."""
        sw, sh = source.get_size()
        if sw <= 0 or sh <= 0:
            return
        tw, th = max(1, int(round(sw * render_scale))), max(1, int(round(sh * render_scale)))
        try:
            tile = pygame.transform.scale(source, (tw, th))
        except pygame.error:
            return
        y = dy
        while y < dy + dh:
            x = dx
            while x < dx + dw:
                vw, vh = min(tw, dx + dw - x), min(th, dy + dh - y)
                if vw > 0 and vh > 0:
                    target.blit(tile, (x, y), pygame.Rect(0, 0, vw, vh))
                x += tw
            y += th

    def _build_path_index(self) -> None:
        self._path_to_index: dict[str, int] = {}
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

    def get_tile_properties(
        self,
        ttype: int,
        variant: int,
        placement: dict[str, object] | None = None,
    ) -> dict[str, object]:
        props: dict[str, object] = {}
        if 0 <= ttype < len(self.parsed.tilesets):
            lower = self.parsed.tilesets[ttype].tile_properties.get(str(variant))
            if isinstance(lower, dict):
                props.update(lower)
        if isinstance(placement, dict):
            props.update(placement)
        return props

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
    def tile_size(self) -> tuple[int, int]:
        return self.parsed.meta.tile_size

    @property
    def map_size(self) -> tuple[int, int]:
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
        layer_type: str | None = None,
        sort_by_zindex: bool = True,
    ) -> list[ParsedLayer]:
        layers = self.parsed.layers
        if layer_type is not None:
            layers = [layer for layer in layers if layer.layer_type == layer_type]
        if not include_hidden:
            layers = [layer for layer in layers if layer.visible]
        if sort_by_zindex:
            layers = sorted(layers, key=lambda layer: (layer.z_index, layer.id))
        return list(layers)

    def get_layer(self, layer_id_or_name: int | str) -> ParsedLayer | None:
        if isinstance(layer_id_or_name, int):
            for layer in self.parsed.layers:
                if layer.id == layer_id_or_name:
                    return layer
            return None
        for layer in self.parsed.layers:
            if layer.name == layer_id_or_name:
                return layer
        return None

    def get_tile_layers_dict(self, *, include_hidden: bool = True) -> dict[int, ParsedLayer]:
        return {
            layer.id: layer
            for layer in self.get_layers(include_hidden=include_hidden, layer_type="tile", sort_by_zindex=False)
        }

    def build_tile_map(
        self,
        exclude_layers: set[str] | None = None,
        use_gids: bool = False,
    ) -> dict[tuple[int, int], tuple[tuple[int, int], ...]]:
        """Build a ``{(col, row): ((gid, flipbits), ...)}`` dict for use with
        :class:`tilemap_parser.runtime.movement.CollisionRunner`.

        Godot parity: layers are **unioned**, not overwritten.  Every tile
        layer contributes its ``(gid, flipbits)`` entry at a cell, so an
        upper deco tile can never erase a lower solid tile (each
        ``TileMapLayer`` owns independent physics bodies in Godot), and
        flipped tiles keep their own geometry.  Cells hold entries in
        ``(z_index, id)`` order.  Query code tests *all* entries in a cell.

        Only tile layers are scanned; object layers are skipped
        automatically.  Pass *exclude_layers* to skip specific tile
        layers by name (e.g. collisions, overlays).  Layers with
        ``collision_enabled=False`` are also skipped.

        When *use_gids* is ``True``, the returned gids are global tile
        IDs (firstgid + variant) so that tiles from different tilesets
        with the same variant number produce distinct values.
        """
        from .world import flip_flags as _flip_flags

        tile_map: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {}
        layers = sorted(self.parsed.layers, key=lambda layer: (layer.z_index, layer.id))
        for layer in layers:
            if layer.layer_type != "tile":
                continue
            if exclude_layers and layer.name in exclude_layers:
                continue
            if not getattr(layer, "collision_enabled", True):
                continue
            for (tx, ty), tile in layer.tiles.items():
                if not isinstance(tile.ttype, int):
                    continue
                if use_gids:
                    if tile.gid is not None:
                        gid = tile.gid
                    else:
                        ts_idx = tile.ttype
                        if 0 <= ts_idx < len(self.parsed.tilesets):
                            ts = self.parsed.tilesets[ts_idx]
                            if ts.firstgid:
                                gid = ts.firstgid + tile.variant
                            else:
                                gid = tile.variant
                        else:
                            gid = tile.variant
                else:
                    gid = tile.variant
                entry = (
                    gid,
                    _flip_flags(
                        bool(getattr(tile, "flip_h", False)),
                        bool(getattr(tile, "flip_v", False)),
                        bool(getattr(tile, "flip_d", False)),
                    ),
                )
                existing = tile_map.get((tx, ty))
                if existing is None:
                    tile_map[(tx, ty)] = (entry,)
                elif entry not in existing:
                    tile_map[(tx, ty)] = (*existing, entry)
        return tile_map

    def get_image(self, variant: int, ttype: int = 0, *, copy_surface: bool = True) -> Surface | None:
        if ttype < 0 or ttype >= len(self.surfaces):
            return None
        source = self.surfaces[ttype]
        if source is None:
            return None
        return _variant_surface(source, variant, self.tile_size, copy_surface=copy_surface)

    def get_object_surface(self, obj: ParsedObject, *, copy_surface: bool = True) -> Surface | None:
        """Return the editor-visible surface for one object.

        The editor stores a contiguous tile stamp as a single rect
        (``variant`` = top-left cell, ``area`` = full pixel extent) and
        paints it back as one sheet slice. This mirrors that: a single
        ``Rect(variant_pos, area.w, area.h)`` crop. Returns ``None`` when
        the rect escapes the sheet (e.g. a stamp that wrapped sheet rows,
        which the editor cannot represent either).
        """
        if obj.ttype < 0 or obj.ttype >= len(self.surfaces):
            return None
        source = self.surfaces[obj.ttype]
        if source is None:
            return None
        if (obj.area.w, obj.area.h) == (source.get_width(), source.get_height()):
            return source.copy() if copy_surface else source
        tw, th = self.tile_size
        if tw <= 0 or th <= 0 or obj.area.w <= 0 or obj.area.h <= 0:
            return None
        cols = source.get_width() // tw
        if cols <= 0:
            return None
        src_x = (obj.variant % cols) * tw
        src_y = (obj.variant // cols) * th
        src = Rect(src_x, src_y, obj.area.w, obj.area.h)
        if not source.get_rect().contains(src):
            self.warnings.append(
                f"Object rect variant={obj.variant} area="
                f"({obj.area.x}, {obj.area.y}, {obj.area.w}, {obj.area.h}) "
                f"outside sheet; skipping"
            )
            return None
        cell = source.subsurface(src)
        return cell.copy() if copy_surface else cell

    def get_tile_surface(self, ttype: int, variant: int, *, copy_surface: bool = True) -> Surface | None:
        return self.get_image(variant=variant, ttype=ttype, copy_surface=copy_surface)

    def get_tile_at(self, layer_id_or_name: int | str, x: int, y: int) -> ParsedTile | None:
        layer = self.get_layer(layer_id_or_name)
        if layer is None:
            return None
        return layer.tiles.get((x, y))

    def get_tile_surface_at(self, layer_id_or_name: int | str, x: int, y: int) -> Surface | None:
        tile = self.get_tile_at(layer_id_or_name, x, y)
        if tile is None or not isinstance(tile.ttype, int):
            return None
        return self.get_tile_surface(tile.ttype, tile.variant)

    def get_object_surface_by_id(
        self, layer_id_or_name: int | str, object_id: int, *, copy_surface: bool = True, scaled: bool = False
    ) -> tuple[Surface, float, float] | None:
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
        self, layer_id_or_name: int | str, *, copy_surface: bool = True, scaled: bool = False
    ) -> list[tuple[Surface, float, float, int]]:
        layer = self.get_layer(layer_id_or_name)
        if layer is None or layer.layer_type != "object":
            return []
        result: list[tuple[Surface, float, float, int]] = []
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

    def get_tileset_animation(self, ttype: int) -> dict | None:
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

    def get_object_animation(self, obj: ParsedObject, render_scale: float = 1.0) -> AnimData | None:
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
        anim_data: ObjectAnimation | None = obj.animation  # internal, keep frame_count
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
        frames: list[Surface] = []
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
    tile_size: tuple[int, int],
    *,
    copy_surface: bool,
) -> Surface | None:
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


def _resolve_resource_path(path_str: str, map_dir: Path, extra_search_base: Path | None) -> Path:
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


def _resolve_tile_offset(
    offset_tiles: tuple[int, int] | None,
    offset_x: int | None,
    offset_y: int | None,
) -> tuple[int, int]:
    if offset_tiles is None:
        ox = 0 if offset_x is None else offset_x
        oy = 0 if offset_y is None else offset_y
    else:
        ox, oy = offset_tiles
        if offset_x is not None:
            ox = offset_x
        if offset_y is not None:
            oy = offset_y
    for v in (ox, oy):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"tile offset must be ints, got {(ox, oy)!r}")
    if ox < 0 or oy < 0:
        raise ValueError(f"tile offset must be >= 0, got {(ox, oy)!r}")
    return (ox, oy)


def _apply_tile_offset(parsed: ParsedMap, ox: int, oy: int) -> tuple[int, int]:
    tw, th = parsed.meta.tile_size
    rs = parsed.meta.render_scale
    eff_w = int(tw * rs)
    eff_h = int(th * rs)
    area_dx = ox * tw
    area_dy = oy * th
    for layer in parsed.layers:
        if layer.tiles:
            shifted = {}
            for (x, y), tile in layer.tiles.items():
                new_pos = (x + ox, y + oy)
                tile.pos = new_pos
                shifted[new_pos] = tile
            layer.tiles = shifted
        for obj in layer.objects.values():
            obj.area.x += area_dx
            obj.area.y += area_dy
        if layer.image_rect is not None:
            ix, iy, iw, ih = layer.image_rect
            layer.image_rect = (ix + area_dx, iy + area_dy, iw, ih)
        for placement in layer.image_placements:
            placement.x += area_dx
            placement.y += area_dy
    for node in parsed.nodes:
        node.area.x += area_dx
        node.area.y += area_dy
    parsed.meta.map_size = (parsed.meta.map_size[0] + ox, parsed.meta.map_size[1] + oy)
    parsed.meta.initial_map_size = (
        parsed.meta.initial_map_size[0] + ox,
        parsed.meta.initial_map_size[1] + oy,
    )
    parsed.meta.scroll = (
        parsed.meta.scroll[0] + ox * eff_w,
        parsed.meta.scroll[1] + oy * eff_h,
    )
    return (ox * eff_w, oy * eff_h)


def _normalize_origin(parsed: ParsedMap) -> tuple[int, int]:
    tw, th = parsed.meta.tile_size
    rs = parsed.meta.render_scale
    eff_w = int(tw * rs)
    eff_h = int(th * rs)
    if tw <= 0 or th <= 0 or eff_w <= 0 or eff_h <= 0:
        return (0, 0)

    min_x = 0
    min_y = 0
    max_x = parsed.meta.map_size[0]
    max_y = parsed.meta.map_size[1]

    # NOTE: tile keys are tile units; object/node areas are map px.
    # Both must be measured in tile units here, i.e. areas divide by the
    # *unscaled* tile size. Using the scaled stride undercounts negative
    # spans and over-shifts areas by the render-scale factor downstream.
    for layer in parsed.layers:
        for x, y in layer.tiles.keys():
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + 1)
            max_y = max(max_y, y + 1)

        for obj in layer.objects.values():
            left = math.floor(obj.area.x / tw)
            top = math.floor(obj.area.y / th)
            right = math.ceil((obj.area.x + obj.area.w) / tw)
            bottom = math.ceil((obj.area.y + obj.area.h) / th)
            min_x = min(min_x, left)
            min_y = min(min_y, top)
            max_x = max(max_x, right)
            max_y = max(max_y, bottom)

        if layer.image_rect is not None:
            ix, iy, iw, ih = layer.image_rect
            min_x = min(min_x, math.floor(ix / tw))
            min_y = min(min_y, math.floor(iy / th))
        for placement in layer.image_placements:
            min_x = min(min_x, math.floor(placement.x / tw))
            min_y = min(min_y, math.floor(placement.y / th))

    for node in parsed.nodes:
        left = math.floor(node.area.x / tw)
        top = math.floor(node.area.y / th)
        right = math.ceil((node.area.x + node.area.w) / tw)
        bottom = math.ceil((node.area.y + node.area.h) / th)
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
    # Areas stay in map px, so they shift by unscaled strides; the returned
    # offset (and scroll follow) remain scaled world px as before.
    area_shift_x = shift_x * tw
    area_shift_y = shift_y * th

    for layer in parsed.layers:
        if layer.tiles:
            shifted_tiles = {}
            for (x, y), tile in layer.tiles.items():
                new_pos = (x + shift_x, y + shift_y)
                tile.pos = new_pos
                shifted_tiles[new_pos] = tile
            layer.tiles = shifted_tiles

        for obj in layer.objects.values():
            obj.area.x += area_shift_x
            obj.area.y += area_shift_y

        if layer.image_rect is not None:
            ix, iy, iw, ih = layer.image_rect
            layer.image_rect = (ix + area_shift_x, iy + area_shift_y, iw, ih)
        for placement in layer.image_placements:
            placement.x += area_shift_x
            placement.y += area_shift_y

    for node in parsed.nodes:
        node.area.x += area_shift_x
        node.area.y += area_shift_y

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


def load_map(
    path: PathLike,
    *,
    extra_search_base: Path | None = None,
    skip_missing_images: bool = True,
    nodes_dir: PathLike | None = None,
    offset_tiles: tuple[int, int] | None = None,
    offset_x: int | None = None,
    offset_y: int | None = None,
) -> TilemapData:
    return TilemapData.load(
        path,
        extra_search_base=extra_search_base,
        skip_missing_images=skip_missing_images,
        nodes_dir=nodes_dir,
        offset_tiles=offset_tiles,
        offset_x=offset_x,
        offset_y=offset_y,
    )
