import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import { Link } from "react-router-dom";

export default function QuickStart() {
  return (
    <div className="content">
      <h1>Quick Start</h1>
      <p>
        The smallest thing that loads a map, moves a sprite against tiles, and
        draws. Top-down slide movement: swap the runner preset and the sprite
        contract for a platformer (see{" "}
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

      <h2 id="pieces">WHAT JUST HAPPENED</h2>
      <ul>
        <li>
          <code>load_map</code> parses the tilemap-editor JSON into a{" "}
          <code>TilemapData</code>. The renderer draws it;
          <code>build_tile_map()</code> turns the tile layers into a{" "}
          <code>
            {"{"} (col, row): tile_id {"}"}
          </code>{" "}
          dict the runner iterates.
        </li>
        <li>
          <code>CollisionCache.get_tileset_collision</code> loads the per-tile
          polygons. Tiles with no entry are walkable.
        </li>
        <li>
          <code>CollisionRunner.from_game_type("topdown")</code> = slide mode,
          gravity off. Each frame you hand it a displacement (
          <code>velocity × dt</code>) and it slides the sprite along walls.
        </li>
        <li>
          <code>camera.update(dt)</code> then{" "}
          <code>renderer.render(screen, camera.offset)</code>: the camera
          offsets the world, the renderer culls to the viewport.
        </li>
      </ul>

      <h2 id="platformer">WANT GRAVITY INSTEAD?</h2>
      <p>
        Give the player <code>vx</code>, <code>vy</code>, <code>on_ground</code>
        , build a <code>PhysicsWorld</code> from the map, attach the runner
        once, and call{" "}
        <code>
          runner.move_platformer(player, None, None, dt, input_x=...,
          jump_pressed=...)
        </code>
        . That path, and the crate-pushing it enables, is the whole{" "}
        <Link to="/physics">Physics &amp; Bodies</Link> guide.
      </p>

      <Callout kind="warn" title="TOPLEFT VS CENTER" id="top-left-vs-center">
        <code>RectangleShape</code> anchors <code>(x, y)</code> at its top-left.
        <code>CircleShape</code> anchors <code>(x, y)</code> at its center;{" "}
        <code>CapsuleShape</code> anchors <code>(x, y)</code> at its <em>top
        cap's</em> center. Widths are always full sizes:{" "}
        <code>RectangleShape(width, height)</code> uses your values as-is,
        while <code>CircleShape(radius)</code> and{" "}
        <code>CapsuleShape(radius, height)</code> are half-widths. So when you
        draw (or check bounds):
        <ul>
          <li>rectangle → draw the box at <code>(x, y)</code>, size{" "}
            <code>w × h</code>;</li>
          <li>circle → draw the box at <code>(x - radius, y - radius)</code>,
            size <code>2r × 2r</code>;</li>
          <li>capsule → draw the box at <code>(x - radius, y - radius)</code>,
            size <code>2r × (2r + height)</code>.</li>
        </ul>
        Never halve a rectangle's width, and never draw a circle/capsule at{" "}
        <code>(x, y)</code> — that shifts it up and left by one radius. Swap
        conventions and your sprite teleports half its size into the floor.
      </Callout>
    </div>
  );
}
