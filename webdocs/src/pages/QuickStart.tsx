import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import { Link } from "react-router-dom";

export default function QuickStart() {
  return (
    <div className="content">
      <h1>Quick Start</h1>
      <p>
        A minimal standalone program demonstrating map loading, tile collision resolution, and camera rendering in pygame-ce.
        This example demonstrates top-down slide movement; platformer mechanics with gravity and jumping require setting{" "}
        <code>vx</code>, <code>vy</code>, and <code>on_ground</code> (detailed in{" "}
        <Link to="/physics">Physics &amp; Bodies</Link>).
      </p>

      <CodeBlock
        title="quickstart.py"
        code={`import pygame
from tilemap_parser import (
    Camera, CollisionCache, CollisionRunner, RectangleShape,
    TileLayerRenderer, load_map,
)

pygame.init()
screen = pygame.display.set_mode((800, 600))

# 1. load the map and its tile collision data
game_data = load_map("data/map.json")
renderer  = TileLayerRenderer(game_data)
tileset   = CollisionCache().get_tileset_collision("data/collision/terrain.collision.json")
tile_map  = game_data.build_tile_map()

# 2. a player: any object with x, y, collision_shape
class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.collision_shape = RectangleShape(width=16, height=16)

player = Player(96, 96)
camera = Camera(800, 600, mode="centered")
camera.follow(player)

# 3. collision runner (top-down => slide mode, no gravity)
runner = CollisionRunner.from_game_type("topdown", tile_size=game_data.tile_size)

clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 160.0 * dt
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 160.0 * dt

    runner.move(player, tileset, tile_map, delta_x=dx, delta_y=dy)
    camera.update(dt)

    screen.fill((35, 35, 45))
    renderer.render(screen, camera.offset)
    pygame.display.flip()

pygame.quit()`}
      />

      <h2 id="pieces">Runtime Execution Flow</h2>
      <ul>
        <li>
          <code>load_map</code> parses the tilemap-editor JSON into a{" "}
          <code>TilemapData</code> instance. <code>TileLayerRenderer</code> culls
          and renders visible chunks; <code>build_tile_map()</code> compiles tile
          layers into a <code>{"{"} (col, row): tile_id {"}"}</code> spatial map.
        </li>
        <li>
          <code>CollisionCache.get_tileset_collision</code> parses polygon
          boundaries and custom properties per tile. Tiles without collision
          definitions remain walkable.
        </li>
        <li>
          <code>CollisionRunner.from_game_type("topdown")</code> applies slide
          mode without gravity. Each frame, movement displacement (
          <code>velocity × dt</code>) is resolved with wall sliding.
        </li>
        <li>
          <code>camera.update(dt)</code> updates target tracking, followed by{" "}
          <code>renderer.render(screen, camera.offset)</code> to draw the
          viewport with camera offsets.
        </li>
      </ul>

      <h2 id="platformer">Platformer Configuration & Gravity</h2>
      <p>
        To enable gravity, jumping, and step-up mechanics, provide the sprite with{" "}
        <code>vx</code>, <code>vy</code>, and <code>on_ground</code> attributes.
        Construct a <code>PhysicsWorld</code> from the map, attach the runner,
        and call{" "}
        <code>
          runner.move_platformer(player, None, None, dt, input_x=...,
          jump_pressed=...)
        </code>
        . See the <Link to="/physics">Physics &amp; Bodies</Link> guide for full
        details on pushable bodies and platform dynamics.
      </p>

      <Callout kind="warn" title="Coordinate Anchoring & Shape Sizing" id="top-left-vs-center">
        <code>RectangleShape</code> anchors <code>(x, y)</code> at its top-left.
        <code>CircleShape</code> anchors <code>(x, y)</code> at its center;{" "}
        <code>CapsuleShape</code> anchors <code>(x, y)</code> at its <em>top
        cap's</em> center. Widths are always full sizes:{" "}
        <code>RectangleShape(width, height)</code> uses your values as-is,
        while <code>CircleShape(radius)</code> and{" "}
        <code>CapsuleShape(radius, height)</code> are half-widths. When rendering
        or checking bounding boxes:
        <ul>
          <li>rectangle → draw at <code>(x, y)</code> with dimensions{" "}
            <code>w × h</code>;</li>
          <li>circle → draw at <code>(x - radius, y - radius)</code> with
            dimensions <code>2r × 2r</code>;</li>
          <li>capsule → draw at <code>(x - radius, y - radius)</code> with
            dimensions <code>2r × (2r + height)</code>.</li>
        </ul>
        Do not halve a rectangle's dimensions or offset a circle/capsule origin
        incorrectly, as coordinate mismatches cause sprites to clip into surfaces.
      </Callout>
    </div>
  );
}
