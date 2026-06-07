from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .map_parse import (
    JsonDict,
    MapParseError,
    ParsedObjectArea,
    _coerce_bool,
    _coerce_float,
    _coerce_int,
    _optional_dict,
    _require_dict,
    _require_list,
    _require_str,
    _ctx,
)


@dataclass
class ParsedNode:
    node_id: str
    name: str
    node_type: str
    area: ParsedObjectArea
    layer_name: str
    properties: JsonDict = field(default_factory=dict)
    group: Optional[str] = None


def _parse_area(raw: Any, ctx: str) -> ParsedObjectArea:
    d = _require_dict(raw, ctx)
    return ParsedObjectArea(
        x=_coerce_int(d.get("x"), f"{ctx}.x"),
        y=_coerce_int(d.get("y"), f"{ctx}.y"),
        w=_coerce_int(d.get("w"), f"{ctx}.w"),
        h=_coerce_int(d.get("h"), f"{ctx}.h"),
    )


def _parse_node(raw: Any, ctx: str) -> ParsedNode:
    d = _require_dict(raw, ctx)
    group_raw = d.get("group")
    group = str(group_raw) if group_raw is not None else None
    return ParsedNode(
        node_id=_require_str(d.get("node_id"), f"{ctx}.node_id"),
        name=_require_str(d.get("name"), f"{ctx}.name"),
        node_type=_require_str(d.get("node_type", "area"), f"{ctx}.node_type"),
        area=_parse_area(d.get("area"), f"{ctx}.area"),
        layer_name=_require_str(d.get("layer_name", ""), f"{ctx}.layer_name"),
        properties=_optional_dict(d.get("properties"), f"{ctx}.properties") or {},
        group=group,
    )


def parse_nodes_dict(root: JsonDict) -> List[ParsedNode]:
    root = _require_dict(root, "root")
    raw_nodes = _require_list(root.get("nodes", []), "root.nodes")
    return [_parse_node(item, f"root.nodes[{i}]") for i, item in enumerate(raw_nodes)]


def parse_nodes_file(path: Union[str, Path]) -> List[ParsedNode]:
    p = Path(path)
    if not p.is_file():
        raise MapParseError(f"Not a file: {p}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise MapParseError(f"Cannot read {p}: {e}") from e
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise MapParseError(f"Invalid JSON in {p}: {e}") from e
    return parse_nodes_dict(payload)
