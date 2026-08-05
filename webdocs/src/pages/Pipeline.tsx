import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import FlowDiagram, {
  type FlowEdge,
  type FlowNode,
} from "../components/FlowDiagram";

const BLOCK_NODES: FlowNode[] = [
  {
    id: "build",
    x: 0,
    y: 0,
    w: 256,
    h: 80,
    title: "build_scene()",
    lines: ["hand-rolled tile layer", "loads tileset collision"],
    accent: "amber",
  },
  {
    id: "from_world",
    x: 260,
    y: 0,
    w: 256,
    h: 80,
    title: "from_world(world)",
    lines: ["preset + attach", "None, None tile args"],
    accent: "teal",
  },
  {
    id: "platformer",
    x: 520,
    y: 0,
    w: 256,
    h: 80,
    title: "move_platformer",
    lines: ["player vs tiles + bodies", "gravity, jump, step-up"],
    accent: "blue",
  },
  {
    id: "push",
    x: 0,
    y: 208,
    w: 256,
    h: 80,
    title: "push block",
    lines: ["hit_wall_x → find body", "probe the skin gap"],
    accent: "amber",
  },
  {
    id: "drive",
    x: 260,
    y: 208,
    w: 256,
    h: 80,
    title: "crate drive",
    lines: ["move_grounded velocity=", "crates vs tiles + crates"],
    accent: "teal",
  },
  {
    id: "draw",
    x: 520,
    y: 208,
    w: 256,
    h: 80,
    title: "draw",
    lines: ["bodies draw at (x, y)", "box == visual box"],
    accent: "purple",
  },
];

const BLOCK_EDGES: FlowEdge[] = [
  { from: "build", to: "from_world", fromSide: "right", toSide: "left" },
  { from: "from_world", to: "platformer", fromSide: "right", toSide: "left" },
  { from: "platformer", to: "push" },
  { from: "push", to: "drive", fromSide: "right", toSide: "left" },
  { from: "drive", to: "draw", fromSide: "right", toSide: "left" },
];

const SCRIPT = `import copy
import pygame

from tilemap_parser import (
    Body, CollisionRunner, PhysicsWorld, RectangleShape,
    load_map, load_tileset_collision,
)

TILE = 32
COLS, ROWS = 24, 14
SCREEN_W, SCREEN_H = COLS * TILE, ROWS * TILE
FLOOR_ROW = 12
PUSH_SPEED = 260.0

FULL_TILE = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.collision_shape = RectangleShape(width=24, height=28)


def build_scene():
    """Ground rows + a wall column.  Returns the world and its crates."""
    tile_map = {}
    for x in range(COLS):
        for y in (12, 13):
            tile_map[(x, y)] = 0
    for y in range(8, 12):
        tile_map[(16, y)] = 0

    tileset = load_tileset_collision("data/collision/terrain.collision.json")

    world = PhysicsWorld(tile_map=tile_map, tileset_collision=tileset, tile_size=(TILE, TILE))

    crates = [
        Body(RectangleShape(width=TILE, height=TILE), x=8 * TILE, y=12 * TILE - TILE, mode="kinematic"),
        Body(RectangleShape(width=TILE, height=TILE), x=10 * TILE, y=12 * TILE - TILE, mode="kinematic"),
    ]
    for crate in crates:
        world.add_body(crate)
    return world, crates


def body_ahead(world, sprite, axis, probe=8.0):
    """Find the body the sprite is pressed against.

    The runner stops a sprite just short of a body (sub-pixel skin gap),
    so a static collides_with_body check can miss.  Probe a few px in.
    """
    s = copy.copy(sprite)
    s.x = sprite.x + axis * probe
    return world.collides_with_body(s)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    world, crates = build_scene()
    runner = CollisionRunner.from_world(world, game_type="platformer")
    player = Player(96, 12 * TILE - 28)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        axis = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        jump = keys[pygame.K_SPACE]

        # 1. player vs tiles + bodies
        result = runner.move_platformer(player, None, None, dt, input_x=float(axis), jump_pressed=jump)

        # 2. push: pressed against a kinematic crate?  hand it a velocity
        if result.hit_wall_x and axis != 0:
            block = world.collides_with_body(player)
            if block is None:
                block = body_ahead(world, player, axis)
            if block is not None and block.mode == "kinematic":
                block.vx = axis * PUSH_SPEED

        # 3. drive every crate that has a velocity
        for crate in crates:
            if crate.vx:
                crate_result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, crate.vy))
                if crate_result.hit_wall_x:
                    crate.vx = 0.0

        # 4. draw: world, then sprites at (x, y)
        screen.fill((35, 35, 45))
        for (tx, ty), tile_id in world.tile_map.items():
            pygame.draw.rect(screen, (70, 70, 90), (tx * TILE, ty * TILE, TILE, TILE))
        for body in world.bodies:
            pygame.draw.rect(screen, (230, 150, 60), (body.x, body.y, TILE, TILE))
        pygame.draw.rect(screen, (100, 170, 255), (player.x, player.y, 24, 28))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()`;

export default function Pipeline() {
  return (
    <div className="content">
      <h1>The Pipeline: one world, one runner</h1>
      <p>
        The entire flow in one readable script: load map → build the world →
        attach the runner → move the player → push a kinematic crate → draw
        everything. This is the update loop from{" "}
        <code>docs/physics-world.md</code>, assembled exactly as the examples
        run it.
      </p>

      <CodeBlock title="pipeline.py" code={SCRIPT} />

      <h2 id="blocks">WHAT EACH BLOCK DOES</h2>
      <FlowDiagram title="pipeline" nodes={BLOCK_NODES} edges={BLOCK_EDGES} />
      <table>
        <thead>
          <tr>
            <th>Block</th>
            <th>Job</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>build_scene()</code>
            </td>
            <td>
              Hand-rolls the collision tile layer and loads the tileset
              collision. The world owns tiles, geometry and bodies.{" "}
              <code>add_body</code> is what makes crates solid.
            </td>
          </tr>
          <tr>
            <td>
              <code>
                CollisionRunner.from_world(world, game_type="platformer")
              </code>
            </td>
            <td>
              Preset + attach in one call. From here, <code>None, None</code>{" "}
              tile args mean "use the world".
            </td>
          </tr>
          <tr>
            <td>
              <code>move_platformer(...)</code>
            </td>
            <td>
              Player vs tiles + bodies: gravity, jump, step-up, landings.
              Returns the result you branch on.
            </td>
          </tr>
          <tr>
            <td>Push block</td>
            <td>
              On <code>hit_wall_x</code>, identify the solid (
              <code>collides_with_body</code>, probing for the skin gap), and
              only kinematic bodies get a velocity.
            </td>
          </tr>
          <tr>
            <td>Crate drive</td>
            <td>
              <code>move_grounded(crate, ..., velocity=...)</code>: explicit
              velocity, no gravity. The runner resolves the crate against tiles{" "}
              <em>and other crates</em>; <code>hit_wall_x</code> stops it.
            </td>
          </tr>
          <tr>
            <td>Draw</td>
            <td>
              Sprites and bodies draw at their <code>(x, y)</code>; the
              collision box and visual box are the same rectangle.
            </td>
          </tr>
        </tbody>
      </table>

      <h2 id="skip">WHAT BREAKS IF YOU SKIP A STEP</h2>
      <ul>
        <li>
          <strong>
            Skip <code>add_body</code>
          </strong>{" "}
          → crates are invisible to physics; the player walks through them.
        </li>
        <li>
          <strong>
            Skip <code>from_world</code>/<code>attach</code>
          </strong>{" "}
          → the runner never sees the world's tiles or bodies; the player falls
          through the floor.
        </li>
        <li>
          <strong>
            Skip the <code>velocity=</code>
          </strong>{" "}
          → the crate gets gravity and drops; or worse, nothing moves it at all.
        </li>
        <li>
          <strong>Skip the probe</strong> → pushes randomly fail right at the
          moment of contact.
        </li>
      </ul>
      <Callout kind="tip" title="FROM HERE">
        The full object contract and each <code>move_*</code>'s input model are
        on <a href="/physics">Physics &amp; Bodies</a>. Tunables and presets
        live on the <a href="/runner">CollisionRunner guide</a>.
      </Callout>
    </div>
  );
}
