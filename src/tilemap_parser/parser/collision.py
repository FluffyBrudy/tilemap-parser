"""
Collision data parser for tilemap collision systems.

Provides parsing of collision data from JSON into data classes:
- Tileset collision (grid-based polygon shapes)
- Character collision (geometric shapes: rect, circle, capsule, polygon)
- Object collision (region-based polygon paint with layer/mask per region)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

JsonDict = Dict[str, Any]
Point = Tuple[float, float]
IntPoint = Tuple[int, int]


class CollisionParseError(ValueError):
    """Raised when collision data cannot be parsed"""
    pass


@dataclass
class CollisionPolygon:
    """Polygon collision shape for a tile"""

    vertices: List[Point]
    one_way: bool = False

    def transform(self, tile_x: float, tile_y: float, scale: float = 1.0) -> "CollisionPolygon":
        """Transform polygon to world space coordinates"""
        world_vertices = [(tile_x + vx * scale, tile_y + vy * scale) for vx, vy in self.vertices]
        return CollisionPolygon(vertices=world_vertices, one_way=self.one_way)

    def is_valid(self) -> bool:
        """Check if polygon has at least 3 vertices"""
        return len(self.vertices) >= 3


@dataclass
class TileCollisionData:
    """Collision data for a single tile"""

    tile_id: int
    shapes: List[CollisionPolygon] = field(default_factory=list)

    def has_collision(self) -> bool:
        """Check if tile has any valid collision shapes"""
        return any(shape.is_valid() for shape in self.shapes)


@dataclass
class TilesetCollision:
    """Complete collision data for a tileset"""

    tileset_name: str
    tile_size: IntPoint
    tiles: Dict[int, TileCollisionData] = field(default_factory=dict)

    def get_tile_collision(self, tile_id: int) -> Optional[TileCollisionData]:
        """Get collision data for a specific tile"""
        return self.tiles.get(tile_id)

    def has_collision(self, tile_id: int) -> bool:
        """Check if tile has collision data"""
        tile_data = self.get_tile_collision(tile_id)
        return tile_data is not None and tile_data.has_collision()

    def get_world_shapes(
        self, tile_id: int, tile_x: float, tile_y: float, scale: float = 1.0
    ) -> List[CollisionPolygon]:
        """Get collision shapes transformed to world space"""
        tile_data = self.get_tile_collision(tile_id)
        if not tile_data:
            return []
        return [shape.transform(tile_x, tile_y, scale) for shape in tile_data.shapes]

    @classmethod
    def merge(
        cls,
        collisions: List["TilesetCollision"],
        firstgids: List[int],
    ) -> "TilesetCollision":
        """Merge multiple tileset collisions into one, offsetting keys by firstgid.

        Each collision's tiles are re-keyed as ``firstgid + local_id`` so that
        the resulting dict uses global tile IDs for lookup.

        Args:
            collisions: List of TilesetCollision objects to merge.
            firstgids: List of firstgid offsets, one per collision, in the
                       same order as *collisions*.  The offset is added to
                       each tile's local ID to produce the global key.

        Usage::

            merged = TilesetCollision.merge([ts0, ts1], [0, 200])
        """
        if not collisions:
            return cls(tileset_name="merged", tile_size=(0, 0))
        tile_size = collisions[0].tile_size
        merged_tiles: Dict[int, TileCollisionData] = {}
        for coll, offset in zip(collisions, firstgids, strict=True):
            for local_id, data in coll.tiles.items():
                gid = offset + local_id
                merged_tiles[gid] = TileCollisionData(
                    tile_id=gid,
                    shapes=data.shapes[:],
                )
        return cls(
            tileset_name="merged",
            tile_size=tile_size,
            tiles=merged_tiles,
        )


@dataclass
class RectangleShape:
    """Rectangle collision shape"""

    width: float
    height: float
    offset: Point = (0.0, 0.0)

    def get_bounds(self, x: float, y: float) -> Tuple[float, float, float, float]:
        """Get AABB bounds in world space (left, top, right, bottom)"""
        left = x + self.offset[0]
        top = y + self.offset[1]
        return (left, top, left + self.width, top + self.height)


@dataclass
class CircleShape:
    """Circle collision shape"""

    radius: float
    offset: Point = (0.0, 0.0)

    def get_center(self, x: float, y: float) -> Point:
        """Get center position in world space"""
        return (x + self.offset[0], y + self.offset[1])


@dataclass
class CapsuleShape:
    """Capsule collision shape (vertical orientation)"""

    radius: float
    height: float
    offset: Point = (0.0, 0.0)

    def get_top_center(self, x: float, y: float) -> Point:
        """Get top circle center in world space"""
        return (x + self.offset[0], y + self.offset[1])

    def get_bottom_center(self, x: float, y: float) -> Point:
        """Get bottom circle center in world space"""
        return (x + self.offset[0], y + self.offset[1] + self.height)


CharacterShapeType = Union[RectangleShape, CircleShape, CapsuleShape, CollisionPolygon]


@dataclass
class CharacterCollision:
    """Complete collision data for a character sprite or dynamic object."""

    name: str
    shape: CharacterShapeType
    properties: Dict[str, Any] = field(default_factory=dict)
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF


@dataclass
class ObjectCollisionRegionData:
    """A single collision region within an object collision file."""

    region_id: str
    name: str
    region_rect: Tuple[int, int, int, int]  # (x, y, width, height)
    shapes: List[CollisionPolygon] = field(default_factory=list)
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF
    properties: Dict[str, Any] = field(default_factory=dict)

    def has_collision(self) -> bool:
        """Check if region has any valid collision shapes."""
        return any(shape.is_valid() for shape in self.shapes)

    def get_world_shapes(
        self, world_x: float, world_y: float
    ) -> List[CollisionPolygon]:
        """Get collision shapes transformed to world space using region_rect offset."""
        ox = world_x + self.region_rect[0]
        oy = world_y + self.region_rect[1]
        return [shape.transform(ox, oy) for shape in self.shapes]


@dataclass
class ObjectCollisionData:
    """Complete collision data for object/region-based collision (polygon paint)."""

    tileset_name: str
    regions: Dict[str, ObjectCollisionRegionData] = field(default_factory=dict)

    def get_region(self, region_id: str) -> Optional[ObjectCollisionRegionData]:
        """Get a specific region by ID."""
        return self.regions.get(region_id)

    def has_collision(self, region_id: str) -> bool:
        """Check if a region has collision data."""
        region = self.get_region(region_id)
        return region is not None and region.has_collision()


def parse_tileset_collision(data: JsonDict) -> TilesetCollision:
    """
    Parse tileset collision data from dictionary.

    Args:
        data: Dictionary loaded from .collision.json file

    Returns:
        TilesetCollision object

    Raises:
        CollisionParseError: If data format is invalid
    """
    try:
        tileset_name = data["tileset_name"]
        tile_size_raw = data["tile_size"]
        tile_size = (int(tile_size_raw[0]), int(tile_size_raw[1]))

        tiles: Dict[int, TileCollisionData] = {}
        tiles_data = data.get("tiles", {})

        for tile_id_str, tile_data in tiles_data.items():
            tile_id = int(tile_id_str)
            shapes: List[CollisionPolygon] = []

            for shape_data in tile_data.get("shapes", []):
                vertices = [tuple(v) for v in shape_data["vertices"]]
                one_way = shape_data.get("one_way", False)
                shapes.append(CollisionPolygon(vertices=vertices, one_way=one_way))

            tiles[tile_id] = TileCollisionData(tile_id=tile_id, shapes=shapes)

        return TilesetCollision(
            tileset_name=tileset_name, tile_size=tile_size, tiles=tiles,
        )
    except (KeyError, ValueError, TypeError) as e:
        raise CollisionParseError(f"Invalid tileset collision data: {e}") from e


def parse_character_collision(data: JsonDict) -> CharacterCollision:
    """
    Parse character collision data from dictionary.

    Args:
        data: Dictionary loaded from .collision.json file

    Returns:
        CharacterCollision object

    Raises:
        CollisionParseError: If data format is invalid
    """
    try:
        name = data["name"]
        shape_data = data["shape"]
        shape_type = shape_data["type"]
        offset = tuple(shape_data.get("offset", (0.0, 0.0)))

        if shape_type == "rectangle":
            shape = RectangleShape(
                width=float(shape_data["width"]),
                height=float(shape_data["height"]),
                offset=offset,
            )
        elif shape_type == "circle":
            shape = CircleShape(radius=float(shape_data["radius"]), offset=offset)
        elif shape_type == "capsule":
            shape = CapsuleShape(
                radius=float(shape_data["radius"]),
                height=float(shape_data["height"]),
                offset=offset,
            )
        elif shape_type == "polygon":
            vertices_raw = shape_data.get("vertices")
            if vertices_raw is None:
                raise CollisionParseError("Polygon shape missing 'vertices' field")
            vertices = [tuple(v) for v in vertices_raw]
            if len(vertices) < 3:
                raise CollisionParseError(
                    f"Polygon must have at least 3 vertices, got {len(vertices)}"
                )
            one_way = shape_data.get("one_way", False)
            shape = CollisionPolygon(vertices=vertices, one_way=one_way)
        else:
            raise CollisionParseError(f"Unknown shape type: {shape_type}")

        properties = data.get("properties", {})
        collision_layer = int(properties.get("collision_layer", 1))
        collision_mask = int(properties.get("collision_mask", 0xFFFFFFFF))

        return CharacterCollision(
            name=name,
            shape=shape,
            properties=properties,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
        )
    except (KeyError, ValueError, TypeError) as e:
        raise CollisionParseError(f"Invalid character collision data: {e}") from e


def parse_object_collision(data: JsonDict) -> ObjectCollisionData:
    """
    Parse object collision data (region-based polygon paint) from dictionary.

    The editor stores object collision files with a ``regions`` structure where
    each region contains polygon shapes and optional layer/mask properties.

    File format: ``<tileset_name>.object_collision.json``
    Typical path: ``<data_root>/collision/<tileset_name>.object_collision.json``

    Args:
        data: Dictionary loaded from an object collision JSON file.

    Returns:
        ObjectCollisionData object.

    Raises:
        CollisionParseError: If data format is invalid.
    """
    try:
        tileset_name = data["tileset_name"]
        regions: Dict[str, ObjectCollisionRegionData] = {}
        regions_data = data.get("regions", {})

        for region_id, region_data in regions_data.items():
            region_rect_raw = region_data["region_rect"]
            region_rect = (
                int(region_rect_raw[0]),
                int(region_rect_raw[1]),
                int(region_rect_raw[2]),
                int(region_rect_raw[3]),
            )

            shapes: List[CollisionPolygon] = []
            for shape_data in region_data.get("shapes", []):
                vertices = [tuple(v) for v in shape_data["vertices"]]
                one_way = shape_data.get("one_way", False)
                shapes.append(CollisionPolygon(vertices=vertices, one_way=one_way))

            props = region_data.get("properties", {})
            collision_layer = int(props.get("collision_layer", 1))
            collision_mask = int(props.get("collision_mask", 0xFFFFFFFF))

            regions[region_id] = ObjectCollisionRegionData(
                region_id=region_id,
                name=region_data.get("name", ""),
                region_rect=region_rect,
                shapes=shapes,
                collision_layer=collision_layer,
                collision_mask=collision_mask,
                properties=props,
            )

        return ObjectCollisionData(tileset_name=tileset_name, regions=regions)
    except (KeyError, ValueError, TypeError) as e:
        raise CollisionParseError(f"Invalid object collision data: {e}") from e
