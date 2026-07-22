from __future__ import annotations

import base64
import gzip
import logging
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree

from .map_parse import (
    MapParseError,
    ParsedLayer,
    ParsedMap,
    ParsedMeta,
    ParsedProjectState,
    ParsedTile,
    ParsedTileset,
)

log = logging.getLogger(__name__)

TILE_FLIP_H = 0x80000000
TILE_FLIP_V = 0x40000000
TILE_FLIP_D = 0x20000000
TILE_FLIP_HEX = 0x10000000
TILE_FLIP_MASK = 0x0FFFFFFF

FLIP_BIT_NAMES = {
    TILE_FLIP_H: "H",
    TILE_FLIP_V: "V",
    TILE_FLIP_D: "D",
    TILE_FLIP_HEX: "HEX120",
}
FLIP_ALL = TILE_FLIP_H | TILE_FLIP_V | TILE_FLIP_D | TILE_FLIP_HEX


class TmxParseError(MapParseError):
    pass


def _coerce_int(value: Any, ctx: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        raise TmxParseError(f"{ctx}: expected int, got {value!r}") from e


def _coerce_float(value: Any, ctx: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise TmxParseError(f"{ctx}: expected float, got {value!r}") from e


def _require_attr(elem: ElementTree.Element, name: str, ctx: str) -> str:
    value = elem.get(name)
    if value is None:
        raise TmxParseError(f"{ctx}: missing required attribute {name!r}")
    return value


def _decode_flip_flags(
    gid: int,
) -> Tuple[int, bool, bool, bool, bool]:
    flipped = gid & FLIP_ALL
    stripped = gid & TILE_FLIP_MASK
    if flipped:
        bits = "+".join(name for mask, name in FLIP_BIT_NAMES.items() if flipped & mask)
        log.debug("Tile GID 0x%x has flip flag(s) %s — decoded", gid, bits)
    return (
        stripped,
        bool(gid & TILE_FLIP_H),
        bool(gid & TILE_FLIP_V),
        bool(gid & TILE_FLIP_D),
        bool(gid & TILE_FLIP_HEX),
    )


def _parse_tsx_root(root: ElementTree.Element, source_path: Path) -> dict:
    if root.tag == "tileset":
        tileset = root
    else:
        tileset = root.find("tileset")
    if tileset is None:
        raise TmxParseError(f"TSX {source_path}: missing <tileset> root element")
    return _build_tsx_data(tileset, source_path)


def _build_tsx_data(ts_elem: ElementTree.Element, source_path: Path) -> dict:
    name = ts_elem.get("name", "")
    tilewidth = _coerce_int(_require_attr(ts_elem, "tilewidth", name), f"{name}.tilewidth")
    tileheight = _coerce_int(_require_attr(ts_elem, "tileheight", name), f"{name}.tileheight")
    tilecount = _coerce_int(ts_elem.get("tilecount", 0), f"{name}.tilecount")
    columns = _coerce_int(ts_elem.get("columns", 0), f"{name}.columns")

    image_elem = ts_elem.find("image")
    image_source = ""
    image_width = 0
    image_height = 0
    if image_elem is not None:
        image_source = image_elem.get("source", "")
        image_width = _coerce_int(image_elem.get("width", 0), f"{name}.image.width")
        image_height = _coerce_int(image_elem.get("height", 0), f"{name}.image.height")

    data: dict = {
        "name": name,
        "tilewidth": tilewidth,
        "tileheight": tileheight,
        "tilecount": tilecount,
        "columns": columns,
        "image": image_source,
        "imagewidth": image_width,
        "imageheight": image_height,
    }

    props = _parse_properties(ts_elem)
    if props:
        data["properties"] = props

    tile_properties: Dict[str, Dict[str, Any]] = {}
    for tile_elem in ts_elem.findall("tile"):
        tid = _coerce_int(_require_attr(tile_elem, "id", f"{name}.tile"), f"{name}.tile.id")
        tile_props = _parse_properties(tile_elem)
        if tile_props:
            tile_properties[str(tid)] = tile_props
    if tile_properties:
        data["tile_properties"] = tile_properties

    return data


def _coerce_property_value(value: str, prop_type: str) -> Any:
    if prop_type == "int":
        return int(value)
    elif prop_type == "float":
        return float(value)
    elif prop_type == "bool":
        return value.lower() in ("true", "1")
    elif prop_type == "color":
        return value
    return value


def _parse_properties(elem: ElementTree.Element) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    props_elem = elem.find("properties")
    if props_elem is None:
        return props
    for prop in props_elem.findall("property"):
        prop_name = prop.get("name", "")
        prop_type = prop.get("type", "string")
        raw_value = prop.get("value")
        if raw_value is None:
            raw_value = (prop.text or "").strip()
        props[prop_name] = _coerce_property_value(raw_value, prop_type)
    return props


def _build_embedded_tileset_properties(data: dict) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    if "properties" in data:
        props["properties"] = data["properties"]
    return props


def _build_embedded_tile_properties(data: dict) -> Dict[str, Dict[str, Any]]:
    return data.get("tile_properties", {})


def _tileset_data_to_parsed(data: dict) -> ParsedTileset:
    image_path = data.get("image", "")
    ts_type = "tile"
    props = _build_embedded_tileset_properties(data)
    tile_props = _build_embedded_tile_properties(data)
    return ParsedTileset(
        path=image_path,
        type=ts_type,
        properties=props,
        tile_properties=tile_props,
        animation=None,
    )


def parse_tsx_file(path: Union[str, Path]) -> dict:
    p = Path(path)
    if not p.is_file():
        raise TmxParseError(f"TSX file not found: {p}")
    try:
        tree = ElementTree.parse(p)
    except ElementTree.ParseError as e:
        raise TmxParseError(f"Invalid TSX XML in {p}: {e}") from e
    return _parse_tsx_root(tree.getroot(), p)


def _resolve_image_path(
    raw_path: str, map_dir: Path, tsx_dir: Optional[Path] = None
) -> str:
    if not raw_path:
        return ""
    p = Path(raw_path)
    if p.is_absolute():
        return raw_path
    if tsx_dir:
        candidate = tsx_dir / p
        if candidate.exists():
            return str(candidate)
    candidate = map_dir / p
    if candidate.exists():
        return str(candidate)
    return raw_path


def _decode_csv(text: str) -> List[int]:
    gids: List[int] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        for token in line.split(","):
            token = token.strip()
            if not token:
                continue
            base = 16 if token.lower().startswith("0x") else 10
            gids.append(int(token, base))
    return gids


def _decode_base64(text: str, compression: Optional[str]) -> List[int]:
    try:
        raw = base64.b64decode(text.strip())
        if compression == "zlib":
            raw = zlib.decompress(raw)
        elif compression == "gzip":
            raw = gzip.decompress(raw)
        elif compression:
            raise TmxParseError(
                f"Unsupported tile data compression: {compression!r}"
            )
    except (ValueError, OSError, zlib.error) as e:
        raise TmxParseError(f"Failed to decode tile data: {e}") from e

    if len(raw) % 4 != 0:
        raise TmxParseError(
            f"Tile data payload has {len(raw)} bytes, expected multiple of 4"
        )
    count = len(raw) // 4
    return list(struct.unpack(f"<{count}I", raw))


def _parse_tile_layer(
    layer_elem: ElementTree.Element,
    tilesets: List[Tuple[int, ParsedTileset]],
    ctx: str,
) -> ParsedLayer:
    name = layer_elem.get("name", "Unnamed")
    width = _coerce_int(_require_attr(layer_elem, "width", ctx), f"{ctx}.width")
    height = _coerce_int(_require_attr(layer_elem, "height", ctx), f"{ctx}.height")
    visible = layer_elem.get("visible", "1") != "0"
    opacity = _coerce_float(layer_elem.get("opacity", 1.0), f"{ctx}.opacity")

    layer = ParsedLayer(
        id=0,
        name=name,
        layer_type="tile",
        visible=visible,
        locked=False,
        opacity=opacity,
        z_index=0,
        y_sort=False, y_sort_origin=0,
    )

    layer.properties = _parse_properties(layer_elem)

    data_elem = layer_elem.find("data")
    if data_elem is None:
        return layer

    encoding = data_elem.get("encoding", "xml")
    compression = data_elem.get("compression")
    text = data_elem.text or ""

    if encoding == "csv":
        gids = _decode_csv(text)
    elif encoding == "base64":
        gids = _decode_base64(text, compression)
    else:
        if encoding != "xml":
            log.warning("%s: unsupported encoding %r, treating as xml", ctx, encoding)
        gids = _decode_xml_tiles(data_elem, ctx)

    expected = width * height
    if len(gids) != expected:
        raise TmxParseError(
            f"{ctx}: expected {expected} tile GIDs, got {len(gids)}"
        )

    for idx, raw_gid in enumerate(gids):
        if raw_gid == 0:
            continue
        tx = idx % width
        ty = idx // width
        stripped_gid, flip_h, flip_v, flip_d, flip_hex = _decode_flip_flags(raw_gid)
        ttype, variant = _map_gid(stripped_gid, tilesets, f"{ctx}.tile[{ty},{tx}]")
        if ttype is not None:
            pos = (tx, ty)
            layer.tiles[pos] = ParsedTile(
                pos=pos,
                ttype=ttype,
                variant=variant,
                flip_h=flip_h,
                flip_v=flip_v,
                flip_d=flip_d,
                rotated_hex120=flip_hex,
            )

    return layer


def _decode_xml_tiles(data_elem: ElementTree.Element, ctx: str) -> List[int]:
    gids: List[int] = []
    for tile_elem in data_elem.findall("tile"):
        gid_str = tile_elem.get("gid", "0")
        gids.append(int(gid_str))
    return gids


def _map_gid(
    gid: int,
    tilesets: List[Tuple[int, ParsedTileset]],
    ctx: str,
) -> Tuple[Optional[Union[int, str]], int]:
    for i, (firstgid, ts) in enumerate(tilesets):
        tilecount = int(getattr(ts, "_tilecount", 0))
        if ts.animation is not None:
            tilecount = max(tilecount, ts.animation.frame_count)
        if tilecount > 0:
            if firstgid <= gid < firstgid + tilecount:
                return i, gid - firstgid
        else:
            next_firstgid = tilesets[i + 1][0] if i + 1 < len(tilesets) else float("inf")
            if firstgid <= gid < next_firstgid:
                return i, gid - firstgid
    log.debug("%s: GID %d does not fall into any known tileset range", ctx, gid)
    return None, 0


def _parse_tmx_root(root: ElementTree.Element, map_dir: Path) -> ParsedMap:
    map_elem = root

    tilewidth = _coerce_int(
        _require_attr(map_elem, "tilewidth", "<map>"), "<map>.tilewidth"
    )
    tileheight = _coerce_int(
        _require_attr(map_elem, "tileheight", "<map>"), "<map>.tileheight"
    )
    map_width = _coerce_int(
        _require_attr(map_elem, "width", "<map>"), "<map>.width"
    )
    map_height = _coerce_int(
        _require_attr(map_elem, "height", "<map>"), "<map>.height"
    )

    meta = ParsedMeta(
        tile_size=(tilewidth, tileheight),
        map_size=(map_width, map_height),
        initial_map_size=(map_width, map_height),
        zoom_level=1.0,
        scroll=(0, 0),
        version="1.1",
        render_scale=1.0,
    )

    parsed_tilesets: List[ParsedTileset] = []
    tileset_ranges: List[Tuple[int, ParsedTileset]] = []

    for ts_elem in map_elem.findall("tileset"):
        firstgid = _coerce_int(
            _require_attr(ts_elem, "firstgid", "<tileset>"), "<tileset>.firstgid"
        )
        source = ts_elem.get("source", "")
        if source:
            tsx_path = (map_dir / source).resolve()
            if not tsx_path.is_file():
                log.warning("Referenced TSX not found: %s", tsx_path)
                ts = ParsedTileset(path="", type="tile")
                ts_data: dict = {"tilecount": 0}
            else:
                ts_data = parse_tsx_file(tsx_path)
                ts_data["image"] = _resolve_image_path(
                    ts_data.get("image", ""), map_dir, tsx_path.parent
                )
                ts = _tileset_data_to_parsed(ts_data)
        else:
            ts_data = _build_tsx_data(ts_elem, map_dir)
            ts_data["image"] = _resolve_image_path(
                ts_data.get("image", ""), map_dir, None
            )
            ts = _tileset_data_to_parsed(ts_data)

        tilecount = ts_data.get("tilecount", 0)
        if tilecount == 0 and ts_data.get("imagewidth") and ts_data.get("tilewidth"):
            cols = ts_data["imagewidth"] // ts_data["tilewidth"]
            rows = ts_data["imageheight"] // ts_data["tileheight"]
            tilecount = cols * rows
        if tilecount:
            ts._tilecount = tilecount
        parsed_tilesets.append(ts)
        tileset_ranges.append((firstgid, parsed_tilesets[-1]))
        if tilecount == 0:
            log.warning(
                "Tileset %r (firstgid=%d) has tilecount=0, GID lookup may be imprecise",
                ts_data.get("name", ""),
                firstgid,
            )

    layers: List[ParsedLayer] = []
    for i, layer_elem in enumerate(map_elem.findall("layer")):
        layer = _parse_tile_layer(
            layer_elem, tileset_ranges, f"layer[{i}]"
        )
        layer.id = i
        layer.z_index = i
        layers.append(layer)

    project_state = ParsedProjectState(rules=[], groups=[], automap_rules=None)

    return ParsedMap(
        meta=meta,
        layers=layers,
        tilesets=parsed_tilesets,
        project_state=project_state,
        raw={},
    )


def parse_tmx_file(path: Union[str, Path]) -> ParsedMap:
    p = Path(path)
    if not p.is_file():
        raise TmxParseError(f"TMX file not found: {p}")
    if p.suffix.lower() not in (".tmx", ".xml"):
        raise TmxParseError(f"Expected .tmx file, got {p.suffix!r}")
    try:
        tree = ElementTree.parse(p)
    except ElementTree.ParseError as e:
        raise TmxParseError(f"Invalid TMX XML in {p}: {e}") from e
    return _parse_tmx_root(tree.getroot(), p.parent)
