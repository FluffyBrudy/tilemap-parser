from __future__ import annotations

from typing import Optional, Tuple

from pygame import Rect

from ..parser.node_parse import ParsedNode


class AreaNode:
    def __init__(self, parsed: ParsedNode, render_scale: float = 1.0) -> None:
        self.node_id = parsed.node_id
        self.name = parsed.name
        self.node_type = parsed.node_type
        self.render_scale = render_scale
        rs = render_scale
        self._rect = Rect(
            int(parsed.area.x * rs),
            int(parsed.area.y * rs),
            int(parsed.area.w * rs),
            int(parsed.area.h * rs),
        )
        self.layer_name = parsed.layer_name
        self.properties = dict(parsed.properties)
        self.group = parsed.group

    @property
    def rect(self) -> Rect:
        return self._rect

    @rect.setter
    def rect(self, r: Rect) -> None:
        self._rect = r

    def contains_point(self, point: Tuple[float, float]) -> bool:
        return self._rect.collidepoint(point)

    def overlaps_rect(self, other: Rect) -> bool:
        return self._rect.colliderect(other)

    def __repr__(self) -> str:
        return (
            f"AreaNode(id={self.node_id!r}, name={self.name!r}, "
            f"rect={self._rect}, layer={self.layer_name!r})"
        )
