from __future__ import annotations

from typing import Optional, Tuple

from pygame import Rect

from ..parser.node_parse import ParsedNode


class AreaNode:
    def __init__(self, parsed: ParsedNode) -> None:
        self.node_id = parsed.node_id
        self.name = parsed.name
        self.node_type = parsed.node_type
        self._rect = Rect(parsed.area.x, parsed.area.y, parsed.area.w, parsed.area.h)
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
