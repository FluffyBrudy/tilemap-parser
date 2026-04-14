from __future__ import annotations

import json
import re
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

JsonDict = Dict[str, Any]
Point = Tuple[int, int]
TilesetRef = Union[int, str]


class MapParseError(ValueError):
    pass


def _ctx(path: str, detail: str) -> str:
    return f"{path}: {detail}"


def _require_dict(value: Any, path: str) -> JsonDict:
    if not isinstance(value, dict):
        raise MapParseError(_ctx(path, "expected object"))
    return value


def _require_list(value: Any, path: str) -> List[Any]:
    if not isinstance(value, list):
        raise MapParseError(_ctx(path, "expected array"))
    return value


def _require_str(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise MapParseError(_ctx(path, "expected string"))
    return value


def _coerce_int(value: Any, path: str) -> int:
    if isinstance(value, bool):
        raise MapParseError(_ctx(path, "expected int (got bool)"))
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 10)
        except ValueError as e:
            raise MapParseError(_ctx(path, "expected int")) from e
    raise MapParseError(_ctx(path, "expected int"))


def _coerce_float(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise MapParseError(_ctx(path, "expected number (got bool)"))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as e:
            raise MapParseError(_ctx(path, "expected number")) from e
    raise MapParseError(_ctx(path, "expected number"))


def _coerce_bool(value: Any, path: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    raise MapParseError(_ctx(path, "expected bool"))


def _optional_dict(value: Any, path: str) -> Optional[JsonDict]:
    if value is None:
        return None
    return _require_dict(value, path)


def _parse_point(text: str, path: str) -> Point:
    if not isinstance(text, str):
        raise MapParseError(_ctx(path, "expected point string"))
    matched = re.search(rf"(-?\d+)[{re.escape(string.punctuation)}](-?\d+)$", text.strip())
    if matched is None:
        raise MapParseError(_ctx(path, f"invalid point {text!r}"))
    return int(matched.group(1)), int(matched.group(2))


def _parse_point_field(raw: Any, path: str, default: Optional[str] = None) -> Point:
    if raw is None and default is not None:
        return _parse_point(default, path)
    if not isinstance(raw, str):
        raise MapParseError(_ctx(path, "expected serialized point string"))
    return _parse_point(raw, path)


@dataclass
class ParsedTile:
    pos: Point
    ttype: TilesetRef
    variant: int
    properties: Optional[JsonDict] = None


@dataclass
class ParsedObjectArea:
    x: int
    y: int
    w: int
    h: int


@dataclass
class ParsedObject:
    area: ParsedObjectArea
    ttype: int
    tileset_type: str
    variant: int
    properties: Optional[JsonDict] = None


@dataclass
class ParsedTileset:
    path: str
    type: str
    properties: JsonDict = field(default_factory=dict)
    tile_properties: Dict[str, JsonDict] = field(default_factory=dict)


@dataclass
class ParsedLayer:
    id: int
    name: str
    layer_type: str
    visible: bool
    locked: bool
    opacity: float
    z_index: int
    properties: JsonDict = field(default_factory=dict)
    tiles: Dict[Point, ParsedTile] = field(default_factory=dict)
    objects: Dict[int, ParsedObject] = field(default_factory=dict)
    next_object_id: Optional[int] = None


@dataclass
class ParsedAutotileRule:
    name: str
    neighbors: List[Point]
    tileset_path: str
    tileset_index: Optional[int]
    variant_ids: List[int]
    group_id: Optional[Any] = None
    raw: JsonDict = field(default_factory=dict)


@dataclass
class ParsedAutotileGroup:
    name: str
    rules: List[ParsedAutotileRule]


@dataclass
class ParsedMeta:
    tile_size: Point
    map_size: Point
    initial_map_size: Point
    zoom_level: float
    scroll: Point
    version: str


@dataclass
class ParsedProjectState:
    rules: List[ParsedAutotileRule]
    groups: List[ParsedAutotileGroup]
    automap_rules: Any


@dataclass
class ParsedMap:
    meta: ParsedMeta
    layers: List[ParsedLayer]
    tilesets: List[ParsedTileset]
    project_state: ParsedProjectState
    raw: JsonDict


def _parse_tile(tile_data: JsonDict, ctx: str) -> ParsedTile:
    pos = _parse_point(_require_str(tile_data.get("pos"), f"{ctx}.pos"), f"{ctx}.pos")
    variant = _coerce_int(tile_data.get("variant"), f"{ctx}.variant")
    ttype_raw = tile_data.get("ttype", 0)
    if isinstance(ttype_raw, str):
        ttype: TilesetRef = ttype_raw
    else:
        ttype = _coerce_int(ttype_raw, f"{ctx}.ttype")
    props = _optional_dict(tile_data.get("properties"), f"{ctx}.properties")
    return ParsedTile(pos=pos, ttype=ttype, variant=variant, properties=props)


def _parse_tiles(tiles_obj: JsonDict, ctx: str) -> Dict[Point, ParsedTile]:
    result: Dict[Point, ParsedTile] = {}
    for key, value in tiles_obj.items():
        tile_dict = _require_dict(value, f"{ctx}[{key!r}]")
        tile = _parse_tile(tile_dict, f"{ctx}[{key!r}]")
        result[tile.pos] = tile
    return result


def _parse_object_area(area_obj: JsonDict, ctx: str) -> ParsedObjectArea:
    return ParsedObjectArea(
        x=_coerce_int(area_obj.get("x"), f"{ctx}.x"),
        y=_coerce_int(area_obj.get("y"), f"{ctx}.y"),
        w=_coerce_int(area_obj.get("w"), f"{ctx}.w"),
        h=_coerce_int(area_obj.get("h"), f"{ctx}.h"),
    )


def _parse_objects(objs_obj: JsonDict, ctx: str) -> Dict[int, ParsedObject]:
    result: Dict[int, ParsedObject] = {}
    for key, value in objs_obj.items():
        oid = _coerce_int(key, f"{ctx}.<id>")
        obj_dict = _require_dict(value, f"{ctx}.{key}")
        area_dict = _require_dict(obj_dict.get("area"), f"{ctx}.{key}.area")
        area = _parse_object_area(area_dict, f"{ctx}.{key}.area")
        ttype = _coerce_int(obj_dict.get("ttype"), f"{ctx}.{key}.ttype")
        tileset_type = _require_str(obj_dict.get("tileset_type", "object"), f"{ctx}.{key}.tileset_type")
        variant = _coerce_int(obj_dict.get("variant"), f"{ctx}.{key}.variant")
        props = _optional_dict(obj_dict.get("properties"), f"{ctx}.{key}.properties")
        result[oid] = ParsedObject(
            area=area,
            ttype=ttype,
            tileset_type=tileset_type,
            variant=variant,
            properties=props,
        )
    return result


def _parse_layer(layer_obj: JsonDict, layer_id: int, ctx: str) -> ParsedLayer:
    layer = ParsedLayer(
        id=layer_id,
        name=_require_str(layer_obj.get("name"), f"{ctx}.name"),
        layer_type=_require_str(layer_obj.get("type"), f"{ctx}.type"),
        visible=_coerce_bool(layer_obj.get("visible", True), f"{ctx}.visible"),
        locked=_coerce_bool(layer_obj.get("locked", False), f"{ctx}.locked"),
        opacity=_coerce_float(layer_obj.get("opacity", 1.0), f"{ctx}.opacity"),
        z_index=_coerce_int(layer_obj.get("z_index", layer_id), f"{ctx}.z_index"),
        properties=_optional_dict(layer_obj.get("properties"), f"{ctx}.properties") or {},
    )
    layer.tiles = _parse_tiles(_require_dict(layer_obj.get("tiles", {}), f"{ctx}.tiles"), f"{ctx}.tiles")

    if layer.layer_type == "object":
        layer.objects = _parse_objects(_require_dict(layer_obj.get("objects", {}), f"{ctx}.objects"), f"{ctx}.objects")
        if "next_object_id" in layer_obj and layer_obj["next_object_id"] is not None:
            layer.next_object_id = _coerce_int(layer_obj["next_object_id"], f"{ctx}.next_object_id")
    return layer


def _parse_rule(rule_obj: JsonDict, ctx: str) -> ParsedAutotileRule:
    neighbors_raw = _require_list(rule_obj.get("neighbors", []), f"{ctx}.neighbors")
    neighbors: List[Point] = []
    for idx, pair in enumerate(neighbors_raw):
        pair_list = _require_list(pair, f"{ctx}.neighbors[{idx}]")
        if len(pair_list) != 2:
            raise MapParseError(_ctx(f"{ctx}.neighbors[{idx}]", "expected [x, y]"))
        neighbors.append((_coerce_int(pair_list[0], f"{ctx}.neighbors[{idx}][0]"), _coerce_int(pair_list[1], f"{ctx}.neighbors[{idx}][1]")))

    variants_raw = _require_list(rule_obj.get("variant_ids", []), f"{ctx}.variant_ids")
    variant_ids = [_coerce_int(v, f"{ctx}.variant_ids[{i}]") for i, v in enumerate(variants_raw)]
    tileset_path = _require_str(rule_obj.get("tileset_path", ""), f"{ctx}.tileset_path")
    tileset_index_raw = rule_obj.get("tileset_index")
    tileset_index = _coerce_int(tileset_index_raw, f"{ctx}.tileset_index") if tileset_index_raw is not None else None
    return ParsedAutotileRule(
        name=_require_str(rule_obj.get("name"), f"{ctx}.name"),
        neighbors=neighbors,
        tileset_path=tileset_path,
        tileset_index=tileset_index,
        variant_ids=variant_ids,
        group_id=rule_obj.get("group_id"),
        raw=dict(rule_obj),
    )


def _parse_group(group_obj: JsonDict, ctx: str) -> ParsedAutotileGroup:
    rules_raw = _require_list(group_obj.get("rules", []), f"{ctx}.rules")
    rules = [_parse_rule(_require_dict(r, f"{ctx}.rules[{i}]"), f"{ctx}.rules[{i}]") for i, r in enumerate(rules_raw)]
    return ParsedAutotileGroup(name=_require_str(group_obj.get("name"), f"{ctx}.name"), rules=rules)


def _parse_tilesets_list(tilesets_raw: List[Any], ctx: str) -> List[ParsedTileset]:
    out: List[ParsedTileset] = []
    for i, ts in enumerate(tilesets_raw):
        if isinstance(ts, str):
            out.append(ParsedTileset(path=ts, type="tile"))
            continue
        ts_obj = _require_dict(ts, f"{ctx}[{i}]")
        path = _require_str(ts_obj.get("path"), f"{ctx}[{i}].path")
        ts_type = _require_str(ts_obj.get("type", "tile"), f"{ctx}[{i}].type")
        props = _optional_dict(ts_obj.get("properties"), f"{ctx}[{i}].properties") or {}
        tile_props: Dict[str, JsonDict] = {}
        raw_tile_props = ts_obj.get("tile_properties")
        if raw_tile_props is not None:
            tp_obj = _require_dict(raw_tile_props, f"{ctx}[{i}].tile_properties")
            for k, v in tp_obj.items():
                tile_props[str(k)] = _require_dict(v, f"{ctx}[{i}].tile_properties[{k!r}]")
        out.append(ParsedTileset(path=path, type=ts_type, properties=props, tile_properties=tile_props))
    return out


def _parse_resources(resources_raw: Any, ctx: str) -> List[ParsedTileset]:
    if isinstance(resources_raw, list):
        return _parse_tilesets_list(resources_raw, f"{ctx} (list form)")
    resources_obj = _require_dict(resources_raw, ctx)
    tilesets_raw = _require_list(resources_obj.get("tilesets", []), f"{ctx}.tilesets")
    return _parse_tilesets_list(tilesets_raw, f"{ctx}.tilesets")


def _expand_ongrid_to_layer(data_obj: JsonDict, ctx: str) -> List[ParsedLayer]:
    raw_ongrid = _require_dict(data_obj.get("ongrid", {}), f"{ctx}.ongrid")
    layer = ParsedLayer(
        id=0,
        name="Terrain",
        layer_type="tile",
        visible=True,
        locked=False,
        opacity=1.0,
        z_index=0,
        properties={},
    )
    for loc_str, tile_data in raw_ongrid.items():
        tile_dict = _require_dict(tile_data, f"{ctx}.ongrid[{loc_str!r}]")
        if "pos" not in tile_dict:
            tile_dict = {**tile_dict, "pos": str(loc_str)}
        tile = _parse_tile(tile_dict, f"{ctx}.ongrid[{loc_str!r}]")
        layer.tiles[tile.pos] = tile
    return [layer]


def parse_map_dict(root: JsonDict) -> ParsedMap:
    root = _require_dict(root, "root")
    meta_obj = _require_dict(root.get("meta"), "meta")
    tile_size = _parse_point_field(meta_obj.get("tile_size"), "meta.tile_size")
    map_size = _parse_point_field(meta_obj.get("map_size"), "meta.map_size", default=f"{tile_size[0]};{tile_size[1]}")
    init_raw = meta_obj.get("initial_map_size")
    initial_map_size = map_size if init_raw is None else _parse_point_field(init_raw, "meta.initial_map_size")

    meta = ParsedMeta(
        tile_size=tile_size,
        map_size=map_size,
        initial_map_size=initial_map_size,
        zoom_level=_coerce_float(meta_obj.get("zoom_level", 1.0), "meta.zoom_level"),
        scroll=_parse_point_field(meta_obj.get("scroll"), "meta.scroll", default="0;0"),
        version=_require_str(meta_obj.get("version", "1.1"), "meta.version"),
    )

    data_obj = _require_dict(root.get("data"), "data")
    layers_raw = data_obj.get("layers")
    if layers_raw is None:
        layers: List[ParsedLayer] = []
    else:
        layers = [
            _parse_layer(_require_dict(layer, f"data.layers[{i}]"), i, f"data.layers[{i}]")
            for i, layer in enumerate(_require_list(layers_raw, "data.layers"))
        ]
    if not layers:
        layers = _expand_ongrid_to_layer(data_obj, "data")

    project_obj = _require_dict(root.get("project_state", {}), "project_state")
    rules = [
        _parse_rule(_require_dict(rule, f"project_state.rules[{i}]"), f"project_state.rules[{i}]")
        for i, rule in enumerate(_require_list(project_obj.get("rules", []), "project_state.rules"))
    ]
    groups = [
        _parse_group(_require_dict(group, f"project_state.groups[{i}]"), f"project_state.groups[{i}]")
        for i, group in enumerate(_require_list(project_obj.get("groups", []), "project_state.groups"))
    ]
    project_state = ParsedProjectState(rules=rules, groups=groups, automap_rules=project_obj.get("automap_rules"))

    tilesets = _parse_resources(root.get("resources", {}), "resources")
    return ParsedMap(meta=meta, layers=layers, tilesets=tilesets, project_state=project_state, raw=root)


def parse_map_json(text: str) -> ParsedMap:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise MapParseError(f"Invalid JSON: {e}") from e
    return parse_map_dict(_require_dict(payload, "root"))


def parse_map_file(path: Union[str, Path]) -> ParsedMap:
    p = Path(path)
    if not p.is_file():
        raise MapParseError(f"Not a file: {p}")
    if p.suffix.lower() != ".json":
        raise MapParseError(f"Expected .json map file, got {p.suffix!r}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise MapParseError(f"Cannot read {p}: {e}") from e
    return parse_map_json(text)
