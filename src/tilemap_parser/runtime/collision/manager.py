from __future__ import annotations

import warnings
from collections.abc import Iterable, Iterator
from math import floor, isfinite

from ..protocols import ICollidable
from ...utils.geometry import get_shape_aabb
from .hit import CollisionHit, check_collision
from .shapes import _combined_aabb, _get_shapes


class ObjectCollisionManager:
    """
    Uniform grid rebuilt per all-vs-all query; linear scan for single.
    """

    def __init__(
        self,
        objects: Iterable[ICollidable] | None = None,
        *,
        cell_size: float = 128.0,
    ) -> None:
        if not isfinite(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be a finite positive number")

        self.objects: list[ICollidable] = []
        self.cell_size = float(cell_size)
        if objects is not None:
            for obj in objects:
                self.add_object(obj)

    def __len__(self) -> int:
        """Return the number of objects currently managed."""
        return len(self.objects)

    def __iter__(self) -> Iterator[ICollidable]:
        """Iterate over managed objects in insertion order."""
        return iter(self.objects)

    def __contains__(self, obj: object) -> bool:
        """Return True if the exact object instance is managed."""
        return any(existing is obj for existing in self.objects)

    def _find_object_index(self, obj: ICollidable) -> int:
        for index, existing in enumerate(self.objects):
            if existing is obj:
                return index
        return -1

    def add_object(self, obj: ICollidable) -> None:
        """Refuses shapeless objects with a warning; gate on has_collision."""
        if self._find_object_index(obj) != -1:
            warnings.warn(
                f"Object {obj} is already in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        if not _get_shapes(obj):
            warnings.warn(
                f"Object {obj} has no collision shapes, not added: "
                f"gate on has_collision before adding (render-only objects "
                f"do not belong in the manager).",
                UserWarning,
                stacklevel=2,
            )
            return
        self.objects.append(obj)

    def remove_object(self, obj: ICollidable) -> None:
        index = self._find_object_index(obj)
        if index == -1:
            warnings.warn(
                f"Object {obj} is not in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        del self.objects[index]

    def clear(self) -> None:
        self.objects.clear()

    def _cells_for_aabb(
        self,
        aabb: tuple[float, float, float, float],
    ) -> Iterator[tuple[int, int]]:
        left, top, right, bottom = aabb
        min_cell_x = floor(left / self.cell_size)
        max_cell_x = floor(right / self.cell_size)
        min_cell_y = floor(top / self.cell_size)
        max_cell_y = floor(bottom / self.cell_size)

        for cell_y in range(min_cell_y, max_cell_y + 1):
            for cell_x in range(min_cell_x, max_cell_x + 1):
                yield (cell_x, cell_y)

    def _object_aabb(
        self,
        obj: ICollidable,
    ) -> tuple[float, float, float, float] | None:
        shapes = _get_shapes(obj)
        if not shapes:
            return None
        if len(shapes) == 1:
            return get_shape_aabb(obj.x, obj.y, shapes[0])
        return _combined_aabb(obj.x, obj.y, shapes)

    def _build_spatial_index(
        self,
    ) -> tuple[tuple[ICollidable, ...], dict[tuple[int, int], list[int]]]:
        objects = tuple(self.objects)
        grid: dict[tuple[int, int], list[int]] = {}

        for index, obj in enumerate(objects):
            aabb = self._object_aabb(obj)
            if aabb is None:
                continue
            for cell in self._cells_for_aabb(aabb):
                grid.setdefault(cell, []).append(index)

        return objects, grid

    def _candidate_indices(
        self,
        obj: ICollidable,
        grid: dict[tuple[int, int], list[int]],
    ) -> set[int]:
        aabb = self._object_aabb(obj)
        if aabb is None:
            return set()
        candidates: set[int] = set()
        for cell in self._cells_for_aabb(aabb):
            candidates.update(grid.get(cell, ()))
        return candidates

    def check_all_collisions(self) -> list[CollisionHit]:
        """Each pair at most once (j > i)."""
        objects, grid = self._build_spatial_index()
        hits: list[CollisionHit] = []

        for i, obj in enumerate(objects):
            candidate_indices = self._candidate_indices(obj, grid)
            for j in sorted(candidate_indices):
                if j <= i:
                    continue
                hit = check_collision(objects[i], objects[j])
                if hit is not None:
                    hits.append(hit)
        return hits

    def check_object(self, obj: ICollidable) -> list[CollisionHit]:
        """Subject need not be managed; self skipped by identity; shapeless warns."""
        if not _get_shapes(obj):
            warnings.warn(
                f"Object {obj} has no collision shapes, skipping query: "
                f"gate on has_collision before querying.",
                UserWarning,
                stacklevel=2,
            )
            return []
        hits: list[CollisionHit] = []
        for other in self.objects:
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                hits.append(hit)
        return hits

    def check_object_first(self, obj: ICollidable) -> CollisionHit | None:
        """First hit in insertion order; same subject rules as check_object."""
        if not _get_shapes(obj):
            warnings.warn(
                f"Object {obj} has no collision shapes, skipping query: "
                f"gate on has_collision before querying.",
                UserWarning,
                stacklevel=2,
            )
            return None
        for other in self.objects:
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                return hit
        return None

