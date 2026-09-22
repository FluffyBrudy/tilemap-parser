from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

JsonDict = dict[str, Any]
Point = tuple[float, float]
IntPoint = tuple[int, int]


class CollisionParseError(ValueError):
    pass


@dataclass
class CollisionPolygon:
    vertices: list[Point]
    one_way: bool = False

    def transform(self, tile_x: float, tile_y: float, scale: float = 1.0) -> "CollisionPolygon":
        world_vertices = [(tile_x + vx * scale, tile_y + vy * scale) for vx, vy in self.vertices]
        return CollisionPolygon(vertices=world_vertices, one_way=self.one_way)

    def scaled(self, scale: float) -> "CollisionPolygon":
        return CollisionPolygon(
            vertices=[(vx * scale, vy * scale) for vx, vy in self.vertices],
            one_way=self.one_way,
        )

    def inflated(self, amount: float) -> CollisionPolygon:
        verts = list(self.vertices)
        if len(verts) < 3 or amount == 0:
            return CollisionPolygon(vertices=verts, one_way=self.one_way)
        n = len(verts)
        cx = sum(v[0] for v in verts) / n
        cy = sum(v[1] for v in verts) / n
        edge_normals: list[Point] = []
        for i in range(n):
            x1, y1 = verts[i]
            x2, y2 = verts[(i + 1) % n]
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            edge_normals.append((dy / length, -dx / length) if length > 0 else (0.0, 0.0))
        out: list[Point] = []
        for i in range(n):
            nx = edge_normals[i - 1][0] + edge_normals[i][0]
            ny = edge_normals[i - 1][1] + edge_normals[i][1]
            length = math.hypot(nx, ny)
            if length > 0:
                nx, ny = nx / length, ny / length
            vx, vy = verts[i]
            if (vx - cx) * nx + (vy - cy) * ny < 0:
                nx, ny = -nx, -ny
            out.append((vx + nx * amount, vy + ny * amount))
        return CollisionPolygon(vertices=out, one_way=self.one_way)

    def is_valid(self) -> bool:
        return len(self.vertices) >= 3


@dataclass
class TileCollisionData:
    tile_id: int
    shapes: list[CollisionPolygon] = field(default_factory=list)
    # Mutual layer/mask agreement required; defaults collide with everything.
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF

    def has_collision(self) -> bool:
        return any(shape.is_valid() for shape in self.shapes)


@dataclass
class TilesetCollision:
    tileset_name: str
    tile_size: IntPoint
    tiles: dict[int, TileCollisionData] = field(default_factory=dict)

    def get_tile_collision(self, tile_id: int) -> TileCollisionData | None:
        return self.tiles.get(tile_id)

    def has_collision(self, tile_id: int) -> bool:
        tile_data = self.get_tile_collision(tile_id)
        return tile_data is not None and tile_data.has_collision()

    def get_world_shapes(
        self, tile_id: int, tile_x: float, tile_y: float, scale: float = 1.0
    ) -> list[CollisionPolygon]:
        tile_data = self.get_tile_collision(tile_id)
        if not tile_data:
            return []
        return [shape.transform(tile_x, tile_y, scale) for shape in tile_data.shapes]

    @classmethod
    def merge(
        cls,
        collisions: list["TilesetCollision"],
        firstgids: list[int],
    ) -> "TilesetCollision":
        """Re-keys as firstgid + local_id for global lookup."""
        if not collisions:
            return cls(tileset_name="merged", tile_size=(0, 0))
        tile_size = collisions[0].tile_size
        merged_tiles: dict[int, TileCollisionData] = {}
        for coll, offset in zip(collisions, firstgids, strict=True):
            for local_id, data in coll.tiles.items():
                gid = offset + local_id
                merged_tiles[gid] = TileCollisionData(
                    tile_id=gid,
                    shapes=data.shapes[:],
                    collision_layer=data.collision_layer,
                    collision_mask=data.collision_mask,
                )
        return cls(
            tileset_name="merged",
            tile_size=tile_size,
            tiles=merged_tiles,
        )


@dataclass
class RectangleShape:
    width: float
    height: float
    offset: Point = (0.0, 0.0)

    def get_bounds(self, x: float, y: float) -> tuple[float, float, float, float]:
        left = x + self.offset[0]
        top = y + self.offset[1]
        return (left, top, left + self.width, top + self.height)

    def scaled(self, scale: float) -> "RectangleShape":
        return RectangleShape(
            width=self.width * scale,
            height=self.height * scale,
            offset=(self.offset[0] * scale, self.offset[1] * scale),
        )

    def inflated(self, amount: float) -> RectangleShape:
        amount = max(amount, -min(self.width, self.height) / 2)
        return RectangleShape(
            width=self.width + 2 * amount,
            height=self.height + 2 * amount,
            offset=(self.offset[0] - amount, self.offset[1] - amount),
        )


@dataclass
class CircleShape:
    radius: float
    offset: Point = (0.0, 0.0)

    def get_center(self, x: float, y: float) -> Point:
        return (x + self.offset[0], y + self.offset[1])

    def scaled(self, scale: float) -> "CircleShape":
        return CircleShape(
            radius=self.radius * scale,
            offset=(self.offset[0] * scale, self.offset[1] * scale),
        )

    def inflated(self, amount: float) -> CircleShape:
        return CircleShape(
            radius=max(0.0, self.radius + amount),
            offset=self.offset,
        )


@dataclass
class CapsuleShape:
    radius: float
    height: float
    offset: Point = (0.0, 0.0)

    def get_top_center(self, x: float, y: float) -> Point:
        return (x + self.offset[0], y + self.offset[1])

    def get_bottom_center(self, x: float, y: float) -> Point:
        return (x + self.offset[0], y + self.offset[1] + self.height)

    def scaled(self, scale: float) -> "CapsuleShape":
        return CapsuleShape(
            radius=self.radius * scale,
            height=self.height * scale,
            offset=(self.offset[0] * scale, self.offset[1] * scale),
        )

    def inflated(self, amount: float) -> CapsuleShape:
        return CapsuleShape(
            radius=max(0.0, self.radius + amount),
            height=self.height,
            offset=self.offset,
        )


CharacterShapeType = RectangleShape | CircleShape | CapsuleShape | CollisionPolygon

SpriteShape = RectangleShape | CircleShape | CapsuleShape
# Cast once at load; protocols stay wide for manager assignment.


def flip_character_shape(
    shape: CharacterShapeType,
    sprite_size: tuple[float, float],
    *,
    flip_h: bool = True,
    flip_v: bool = False,
) -> CharacterShapeType:
    """Sprite-local mirror; never mutates; twice is identity. Re-anchor
    the owner after flipping to keep it planted."""
    w, h = float(sprite_size[0]), float(sprite_size[1])
    if not math.isfinite(w) or not math.isfinite(h) or w <= 0 or h <= 0:
        raise ValueError(f"sprite_size must be finite and positive, got {sprite_size!r}")
    if isinstance(shape, RectangleShape):
        ox, oy = shape.offset
        return RectangleShape(
            width=shape.width,
            height=shape.height,
            offset=(
                (w - (ox + shape.width)) if flip_h else ox,
                (h - (oy + shape.height)) if flip_v else oy,
            ),
        )
    if isinstance(shape, CircleShape):
        ox, oy = shape.offset
        return CircleShape(
            radius=shape.radius,
            offset=((w - ox) if flip_h else ox, (h - oy) if flip_v else oy),
        )
    if isinstance(shape, CapsuleShape):
        ox, oy = shape.offset
        return CapsuleShape(
            radius=shape.radius,
            height=shape.height,
            offset=(
                (w - ox) if flip_h else ox,
                (h - (oy + shape.height)) if flip_v else oy,
            ),
        )
    if isinstance(shape, CollisionPolygon):
        verts = [(w - x, y) if flip_h else (x, y) for x, y in shape.vertices]
        verts = [(x, h - y) if flip_v else (x, y) for x, y in verts]
        return CollisionPolygon(vertices=verts, one_way=shape.one_way)
    raise TypeError(f"Cannot flip unknown shape type: {type(shape).__name__}")


@dataclass
class CharacterCollision:
    name: str
    shape: CharacterShapeType
    properties: dict[str, Any] = field(default_factory=dict)
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF

    def scaled(self, scale: float) -> "CharacterCollision":
        return CharacterCollision(
            name=self.name,
            shape=self.shape.scaled(scale),
            properties=dict(self.properties),
            collision_layer=self.collision_layer,
            collision_mask=self.collision_mask,
        )


@dataclass
class ObjectCollisionRegionData:
    region_id: str
    name: str
    region_rect: tuple[int, int, int, int]
    shapes: list[CollisionPolygon] = field(default_factory=list)
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF
    properties: dict[str, Any] = field(default_factory=dict)

    def has_collision(self) -> bool:
        return any(shape.is_valid() for shape in self.shapes)

    def get_world_shapes(
        self, world_x: float, world_y: float
    ) -> list[CollisionPolygon]:
        ox = world_x + self.region_rect[0]
        oy = world_y + self.region_rect[1]
        return [shape.transform(ox, oy) for shape in self.shapes]


@dataclass
class ObjectCollisionData:
    tileset_name: str
    regions: dict[str, ObjectCollisionRegionData] = field(default_factory=dict)

    def get_region(self, region_id: str) -> ObjectCollisionRegionData | None:
        return self.regions.get(region_id)

    def has_collision(self, region_id: str) -> bool:
        region = self.get_region(region_id)
        return region is not None and region.has_collision()


def parse_tileset_collision(data: JsonDict) -> TilesetCollision:
    try:
        tileset_name = data["tileset_name"]
        tile_size_raw = data["tile_size"]
        tile_size = (int(tile_size_raw[0]), int(tile_size_raw[1]))

        tiles: dict[int, TileCollisionData] = {}
        tiles_data = data.get("tiles", {})

        for tile_id_str, tile_data in tiles_data.items():
            tile_id = int(tile_id_str)
            shapes: list[CollisionPolygon] = []

            for shape_data in tile_data.get("shapes", []):
                vertices = [tuple(v) for v in shape_data["vertices"]]
                one_way = shape_data.get("one_way", False)
                shapes.append(CollisionPolygon(vertices=vertices, one_way=one_way))

            props = tile_data.get("properties", {})
            if not isinstance(props, dict):
                raise TypeError(f"tile {tile_id} properties must be an object")
            tiles[tile_id] = TileCollisionData(
                tile_id=tile_id,
                shapes=shapes,
                collision_layer=int(props.get("collision_layer", 1)),
                collision_mask=int(props.get("collision_mask", 0xFFFFFFFF)),
            )

        return TilesetCollision(
            tileset_name=tileset_name, tile_size=tile_size, tiles=tiles,
        )
    except (KeyError, ValueError, TypeError) as e:
        raise CollisionParseError(f"Invalid tileset collision data: {e}") from e


def parse_character_collision(data: JsonDict, render_scale: float = 1.0) -> CharacterCollision:
    """Non-finite/non-positive scale raises; shape scaled unless 1.0."""
    if (
        not isinstance(render_scale, (int, float))
        or not math.isfinite(render_scale)
        or render_scale <= 0
    ):
        raise CollisionParseError(f"render_scale must be finite and > 0, got {render_scale!r}")
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
        ).scaled(render_scale)
    except (KeyError, ValueError, TypeError) as e:
        raise CollisionParseError(f"Invalid character collision data: {e}") from e


def parse_object_collision(data: JsonDict) -> ObjectCollisionData:
    """File: <tileset_name>.object_collision.json under <data_root>/collision/."""
    try:
        tileset_name = data["tileset_name"]
        regions: dict[str, ObjectCollisionRegionData] = {}
        regions_data = data.get("regions", {})

        for region_id, region_data in regions_data.items():
            region_rect_raw = region_data["region_rect"]
            region_rect = (
                int(region_rect_raw[0]),
                int(region_rect_raw[1]),
                int(region_rect_raw[2]),
                int(region_rect_raw[3]),
            )

            shapes: list[CollisionPolygon] = []
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
