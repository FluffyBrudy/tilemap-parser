# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-04-23

### Added
- **Collision Module** (`tilemap_parser.collision`): Parsers for tileset and character collision data
  - `CollisionPolygon`, `TileCollisionData`, `TilesetCollision` models
  - `CharacterCollision` with `RectangleShape`, `CircleShape`, `CapsuleShape`
  - `CollisionCache` for optimized runtime lookups
  - `load_tileset_collision()` and `load_character_collision()` file loaders
- **Collision Runner** (`tilemap_parser.collision_runner`): Ready-to-use movement modes
  - `CollisionRunner` with SLIDE, PLATFORMER, and RPG modes
  - `ICollidableSprite` protocol for easy integration
  - Collision detection utilities (point-in-polygon, rect/polygon, circle/polygon)

## [1.0.0] - 2024-XX-XX

### Features
- Initial release with basic tilemap parsing
- Sprite animation support
- JSON map file loader