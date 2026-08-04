"""Spatial-grid object collision manager."""

from __future__ import annotations

import warnings
from math import floor, isfinite
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

from ..protocols import ICollidableObject
from ...utils.geometry import get_shape_aabb
from .hit import CollisionHit, check_collision
from .shapes import _combined_aabb, _get_shapes


class ObjectCollisionManager:
    """
    Manages collision detection for multiple objects.

    Features:
        - Add / remove objects
        - All-vs-all and one-vs-all queries
        - Layer filtering

    Uses a uniform-grid spatial broadphase for all-vs-all queries
    (rebuilt per query) and a linear scan for single-object queries.
    """

    def __init__(
        self,
        objects: Optional[Iterable[ICollidableObject]] = None,
        *,
        cell_size: float = 128.0,
    ) -> None:
        if not isfinite(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be a finite positive number")

        self.objects: List[ICollidableObject] = []
        self.cell_size = float(cell_size)
        if objects is not None:
            for obj in objects:
                self.add_object(obj)

    def __len__(self) -> int:
        """Return the number of objects currently managed."""
        return len(self.objects)

    def __iter__(self) -> Iterator[ICollidableObject]:
        """Iterate over managed objects in insertion order."""
        return iter(self.objects)

    def __contains__(self, obj: object) -> bool:
        """Return True if the exact object instance is managed."""
        return any(existing is obj for existing in self.objects)

    def _find_object_index(self, obj: ICollidableObject) -> int:
        for index, existing in enumerate(self.objects):
            if existing is obj:
                return index
        return -1

    def add_object(self, obj: ICollidableObject) -> None:
        """Add an object to the collision system."""
        if self._find_object_index(obj) != -1:
            warnings.warn(
                f"Object {obj} is already in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        self.objects.append(obj)

    def remove_object(self, obj: ICollidableObject) -> None:
        """Remove an object from the collision system."""
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
        """Remove all objects from the collision system."""
        self.objects.clear()

    def _cells_for_aabb(
        self,
        aabb: tuple[float, float, float, float],
    ) -> Iterator[Tuple[int, int]]:
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
        obj: ICollidableObject,
    ) -> tuple[float, float, float, float]:
        shapes = _get_shapes(obj)
        if len(shapes) == 1:
            return get_shape_aabb(obj.x, obj.y, shapes[0])
        return _combined_aabb(obj.x, obj.y, shapes)

    def _build_spatial_index(
        self,
    ) -> tuple[Tuple[ICollidableObject, ...], Dict[Tuple[int, int], List[int]]]:
        objects = tuple(self.objects)
        grid: Dict[Tuple[int, int], List[int]] = {}

        for index, obj in enumerate(objects):
            for cell in self._cells_for_aabb(self._object_aabb(obj)):
                grid.setdefault(cell, []).append(index)

        return objects, grid

    def _candidate_indices(
        self,
        obj: ICollidableObject,
        grid: Dict[Tuple[int, int], List[int]],
    ) -> Set[int]:
        candidates: Set[int] = set()
        for cell in self._cells_for_aabb(self._object_aabb(obj)):
            candidates.update(grid.get(cell, ()))
        return candidates

    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check every potentially colliding pair.

        Returns a list of CollisionHit for all colliding pairs.
        Each pair appears at most once (i, j) with j > i.
        """
        objects, grid = self._build_spatial_index()
        hits: List[CollisionHit] = []

        for i, obj in enumerate(objects):
            candidate_indices = self._candidate_indices(obj, grid)
            for j in sorted(candidate_indices):
                if j <= i:
                    continue
                hit = check_collision(objects[i], objects[j])
                if hit is not None:
                    hits.append(hit)
        return hits

    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others using a linear scan.

        The queried object does not need to be managed. If it is managed,
        comparison with itself is skipped by identity.
        """
        hits: List[CollisionHit] = []
        for other in self.objects:
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                hits.append(hit)
        return hits

    def check_object_first(self, obj: ICollidableObject) -> Optional[CollisionHit]:
        """
        Check one object against all others and return the first collision hit.

        Iterates managed objects in insertion order. The queried object
        does not need to be managed; if it is managed, comparison with
        itself is skipped by identity.
        """
        for other in self.objects:
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                return hit
        return None

