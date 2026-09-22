"""v6 contract: protocols chain, SpriteShape export, aliases."""

import sys
from pathlib import Path
from typing import cast, get_type_hints

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    ICollidable,
    ICollidableObject,
    ICollidableSprite,
    RectangleShape,
    SpriteShape,
)
from tilemap_parser.parser.collision import CharacterShapeType


class TestSpriteShape:
    def test_exported_from_top_level(self):
        import tilemap_parser

        assert tilemap_parser.SpriteShape is SpriteShape

    def test_omits_polygon(self):
        args = SpriteShape.__args__
        assert RectangleShape in args
        assert CircleShape in args
        assert CapsuleShape in args
        assert CollisionPolygon not in args

    def test_cast_once_at_load(self):
        shape = CircleShape(radius=8)
        assert cast(SpriteShape, shape) is shape

    def test_character_shape_type_still_all_four(self):
        assert CollisionPolygon in CharacterShapeType.__args__


class TestProtocolChain:
    def test_object_is_alias_of_base(self):
        assert ICollidableObject is ICollidable

    def test_sprite_extends_base(self):
        assert ICollidable in ICollidableSprite.__mro__

    def test_sprite_with_explicit_mask_satisfies_base(self):
        class Enemy:
            x = 0.0
            y = 0.0
            vx = 0.0
            vy = 0.0
            on_ground = False
            collision_shape = RectangleShape(width=8, height=8)
            collision_layer = 2
            collision_mask = 1

        assert isinstance(Enemy(), ICollidableSprite)
        assert isinstance(Enemy(), ICollidable)

    def test_base_requires_layer_and_mask(self):
        hints = get_type_hints(ICollidable)
        assert "collision_layer" in hints
        assert "collision_mask" in hints

    def test_sprite_adds_motion_only(self):
        extra = set(get_type_hints(ICollidableSprite)) - set(get_type_hints(ICollidable))
        assert extra == {"vx", "vy", "on_ground"}
