"""
Bouncing Balls — Object Collision Example

Demonstrates tilemap-parser's object-to-object collision detection:
- Loading collision shapes from JSON
- ObjectCollisionManager for multi-object detection
- Mixed shapes: CircleShape, RectangleShape, CollisionPolygon
- Layer filtering (ghost ball passes through others)
- Simple bounce response using collision normal + depth

Controls:
- ESC: Quit
- R: Reset balls
- G: Toggle ghost ball (layer 2, no collisions)
- F1: Toggle debug lines (collision normals)

Requires: pip install pygame
"""

import pygame
import sys
import random
import math
from pathlib import Path

# Add project src to path so we can import tilemap_parser
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tilemap_parser import (
    load_character_collision,
    load_object_collision,
    ObjectCollisionManager,
    CircleShape,
    RectangleShape,
    CollisionPolygon,
)


# ---------------------------------------------------------------------------
# ShapeObject — base class for all dynamic objects
# ---------------------------------------------------------------------------

class ShapeObject:
    """
    Dynamic object implementing the ICollidableObject protocol.
    Subclasses define the collision shape.
    """

    COLORS = [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
        (255, 180, 100),  # Orange
    ]

    def __init__(self, x, y, vx, vy, layer=1, mask=0xFFFFFFFF, ghost=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ghost = ghost
        self.collision_layer = layer
        self.collision_mask = mask
        self.color = random.choice(self.COLORS) if not ghost else (150, 150, 200)
        self.alpha = 128 if ghost else 255
        self.shape_label = ""  # Overridden by subclasses

    def update(self, dt, width, height):
        """Move and bounce off screen edges."""
        self.x += self.vx * dt
        self.y += self.vy * dt

        half_w, half_h = self._half_size()
        if self.x - half_w < 0:
            self.x = float(half_w)
            self.vx = abs(self.vx)
        elif self.x + half_w > width:
            self.x = float(width - half_w)
            self.vx = -abs(self.vx)

        if self.y - half_h < 0:
            self.y = float(half_h)
            self.vy = abs(self.vy)
        elif self.y + half_h > height:
            self.y = float(height - half_h)
            self.vy = -abs(self.vy)

    def _half_size(self):
        """Return (half_width, half_height) for screen bounce."""
        return (16, 16)

    def draw(self, surface, debug_hits=None):
        raise NotImplementedError

    def _draw_debug_lines(self, surface, debug_hits):
        """Draw collision normal lines if debugging."""
        if not debug_hits:
            return
        pos = (int(self.x), int(self.y))
        for hit in debug_hits:
            if hit.object_a is self or hit.object_b is self:
                end_x = pos[0] + int(hit.normal[0] * hit.depth * 5)
                end_y = pos[1] + int(hit.normal[1] * hit.depth * 5)
                pygame.draw.line(surface, (0, 255, 0), pos, (end_x, end_y), 2)


# ---------------------------------------------------------------------------
# Ball — CircleShape
# ---------------------------------------------------------------------------

class Ball(ShapeObject):
    """Bouncing circle."""

    def __init__(self, x, y, vx, vy, radius, layer=1, mask=0xFFFFFFFF, ghost=False):
        super().__init__(x, y, vx, vy, layer, mask, ghost)
        self.radius = radius
        self.collision_shape = CircleShape(radius=radius, offset=(0, 0))
        self.shape_label = "Circle"

    def _half_size(self):
        return (self.radius, self.radius)

    def draw(self, surface, debug_hits=None):
        pos = (int(self.x), int(self.y))

        if self.alpha < 255:
            surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, self.alpha),
                               (self.radius, self.radius), self.radius)
            surface.blit(surf, (pos[0] - self.radius, pos[1] - self.radius))
        else:
            pygame.draw.circle(surface, self.color, pos, self.radius)

        pygame.draw.circle(surface, (255, 255, 255), pos, self.radius, 2)
        self._draw_debug_lines(surface, debug_hits)


# ---------------------------------------------------------------------------
# Block — RectangleShape
# ---------------------------------------------------------------------------

class Block(ShapeObject):
    """Bouncing rectangle."""

    def __init__(self, x, y, vx, vy, width, height, layer=1, mask=0xFFFFFFFF, ghost=False):
        super().__init__(x, y, vx, vy, layer, mask, ghost)
        self.width = width
        self.height = height
        self.collision_shape = RectangleShape(width=width, height=height, offset=(-width / 2, -height / 2))
        self.shape_label = "Rect"

    def _half_size(self):
        return (self.width / 2, self.height / 2)

    def draw(self, surface, debug_hits=None):
        pos = (int(self.x), int(self.y))
        rect = pygame.Rect(pos[0] - self.width // 2, pos[1] - self.height // 2,
                           self.width, self.height)

        if self.alpha < 255:
            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            surf.fill((*self.color, self.alpha))
            surface.blit(surf, rect.topleft)
        else:
            pygame.draw.rect(surface, self.color, rect)

        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        self._draw_debug_lines(surface, debug_hits)


# ---------------------------------------------------------------------------
# Diamond — CollisionPolygon (convex triangle)
# ---------------------------------------------------------------------------

class Diamond(ShapeObject):
    """Bouncing triangle using CollisionPolygon."""

    def __init__(self, x, y, vx, vy, size=20, layer=1, mask=0xFFFFFFFF, ghost=False):
        super().__init__(x, y, vx, vy, layer, mask, ghost)
        self.size = size
        # Equilateral-ish triangle centered at origin
        self.collision_shape = CollisionPolygon(vertices=[
            (0, -size),
            (-size, size),
            (size, size),
        ])
        self.shape_label = "Poly"

    def _half_size(self):
        return (self.size, self.size)

    def draw(self, surface, debug_hits=None):
        pos = (int(self.x), int(self.y))
        points = [
            (pos[0], pos[1] - self.size),
            (pos[0] - self.size, pos[1] + self.size),
            (pos[0] + self.size, pos[1] + self.size),
        ]

        if self.alpha < 255:
            surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            surf_points = [(self.size, 0), (0, self.size * 2), (self.size * 2, self.size * 2)]
            pygame.draw.polygon(surf, (*self.color, self.alpha), surf_points)
            surface.blit(surf, (pos[0] - self.size, pos[1] - self.size))
        else:
            pygame.draw.polygon(surface, self.color, points)

        pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        self._draw_debug_lines(surface, debug_hits)


# ---------------------------------------------------------------------------
# Wall — static boundary
# ---------------------------------------------------------------------------

class Wall:
    """Static boundary wall implementing ICollidableObject."""

    def __init__(self, x, y, width, height, layer=1, mask=1):
        self.x = float(x)
        self.y = float(y)
        self.collision_shape = RectangleShape(width=width, height=height, offset=(0, 0))
        self.collision_layer = layer
        self.collision_mask = mask

    def draw(self, surface):
        rect = pygame.Rect(int(self.x), int(self.y),
                           int(self.collision_shape.width),
                           int(self.collision_shape.height))
        pygame.draw.rect(surface, (80, 80, 120), rect, 2)


# ---------------------------------------------------------------------------
# TilesetObstacle — static obstacle from object collision JSON
# ---------------------------------------------------------------------------

class TilesetObstacle:
    """Static obstacle loaded from tileset object collision JSON."""

    COLORS = {
        "Rock": (120, 120, 120),
        "Crate": (180, 140, 80),
        "Spike": (200, 80, 80),
    }

    def __init__(self, region, world_x, world_y):
        self.x = float(world_x)
        self.y = float(world_y)
        self.name = region.name
        self.region = region
        self.collision_layer = region.collision_layer
        self.collision_mask = region.collision_mask

        # First shape is the visual/collision shape
        if region.shapes:
            self.collision_shape = region.shapes[0]
        else:
            # Fallback to a small rect
            self.collision_shape = RectangleShape(
                width=region.region_rect[2],
                height=region.region_rect[3],
                offset=(0, 0),
            )

    @property
    def width(self):
        return self.region.region_rect[2]

    @property
    def height(self):
        return self.region.region_rect[3]

    def draw(self, surface):
        color = self.COLORS.get(self.name, (150, 150, 150))

        if isinstance(self.collision_shape, CollisionPolygon):
            points = [
                (int(self.x + v[0]), int(self.y + v[1]))
                for v in self.collision_shape.vertices
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        elif isinstance(self.collision_shape, RectangleShape):
            rect = pygame.Rect(int(self.x), int(self.y),
                               int(self.collision_shape.width),
                               int(self.collision_shape.height))
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)


# ---------------------------------------------------------------------------
# Game class
# ---------------------------------------------------------------------------

class Game:
    """Main game class demonstrating mixed-shape object collision detection."""

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FULLSCREEN = True
    BALL_COUNT = 10      # CircleShape
    BLOCK_COUNT = 10       # RectangleShape
    DIAMOND_COUNT = 10     # CollisionPolygon
    SPEED = 200.0
    BALL_RADIUS = 12
    BLOCK_W = 24
    BLOCK_H = 18
    DIAMOND_SIZE = 14
    OBSTACLE_COUNT = 12

    def __init__(self):
        pygame.init()
        if self.FULLSCREEN:
            flags = pygame.FULLSCREEN | pygame.SCALED
            self.screen = pygame.display.set_mode(
                (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), flags)
        else:
            self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Tilemap-Parser: Mixed-Shape Object Collision")
        self.clock = pygame.time.Clock()
        self.running = True
        self.show_debug = False
        self.ghost_enabled = True

        # Load collision shape from JSON
        data_path = Path(__file__).parent.parent / "data" / "ball.collision.json"
        ball_data = load_character_collision(data_path)
        if ball_data is None:
            print(f"Warning: Could not load {data_path}, using defaults")
            self.ball_radius = self.BALL_RADIUS
            self.ball_layer = 1
            self.ball_mask = 1
        else:
            self.ball_radius = ball_data.shape.radius
            self.ball_layer = ball_data.collision_layer
            self.ball_mask = ball_data.collision_mask
            print(f"Loaded ball shape: radius={self.ball_radius}, "
                  f"layer={self.ball_layer}, mask={self.ball_mask:#x}")

        # Load tileset object collision
        tileset_path = Path(__file__).parent.parent / "data" / "Terrain.object_collision.json"
        self.tileset_data = load_object_collision(tileset_path)
        if self.tileset_data is None:
            print(f"Warning: Could not load {tileset_path}")
        else:
            print(f"Loaded tileset '{self.tileset_data.tileset_name}' with "
                  f"{len(self.tileset_data.regions)} obstacle regions")

        # Collision manager
        self.manager = ObjectCollisionManager()

        # Objects
        self.objects = []
        self.walls = []
        self.obstacles = []
        self.reset()

    def _random_obj(self, half_w, half_h):
        """Generate random position and velocity for an object."""
        x = random.uniform(half_w * 2, self.SCREEN_WIDTH - half_w * 2)
        y = random.uniform(half_h * 2, self.SCREEN_HEIGHT - half_h * 2)
        angle = random.uniform(0, 2 * math.pi)
        speed = self.SPEED * random.uniform(0.5, 1.0)
        return x, y, math.cos(angle) * speed, math.sin(angle) * speed

    def reset(self):
        """Reset all objects to random positions and velocities."""
        # Clear manager
        for obj in self.objects:
            self.manager.remove_object(obj)
        self.objects.clear()

        layer = self.ball_layer
        mask = self.ball_mask

        # Create circle balls
        for _ in range(self.BALL_COUNT):
            x, y, vx, vy = self._random_obj(self.BALL_RADIUS, self.BALL_RADIUS)
            ball = Ball(x, y, vx, vy, self.ball_radius, layer=layer, mask=mask)
            self.objects.append(ball)
            self.manager.add_object(ball)

        # Create rectangle blocks
        for _ in range(self.BLOCK_COUNT):
            x, y, vx, vy = self._random_obj(self.BLOCK_W / 2, self.BLOCK_H / 2)
            block = Block(x, y, vx, vy, self.BLOCK_W, self.BLOCK_H, layer=layer, mask=mask)
            self.objects.append(block)
            self.manager.add_object(block)

        # Create polygon diamonds
        for _ in range(self.DIAMOND_COUNT):
            x, y, vx, vy = self._random_obj(self.DIAMOND_SIZE, self.DIAMOND_SIZE)
            diamond = Diamond(x, y, vx, vy, self.DIAMOND_SIZE, layer=layer, mask=mask)
            self.objects.append(diamond)
            self.manager.add_object(diamond)

        # Create ghost ball (layer 2, mask=0 → no collisions)
        if self.ghost_enabled:
            ghost = Ball(
                self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
                100, 80, self.ball_radius,
                layer=2, mask=0, ghost=True
            )
            self.objects.append(ghost)
            self.manager.add_object(ghost)

        # Create boundary walls
        self.walls.clear()
        wt = 4
        self.walls.append(Wall(0, 0, self.SCREEN_WIDTH, wt))
        self.walls.append(Wall(0, self.SCREEN_HEIGHT - wt, self.SCREEN_WIDTH, wt))
        self.walls.append(Wall(0, 0, wt, self.SCREEN_HEIGHT))
        self.walls.append(Wall(self.SCREEN_WIDTH - wt, 0, wt, self.SCREEN_HEIGHT))
        for wall in self.walls:
            self.manager.add_object(wall)

        # Create tileset obstacles
        self.obstacles.clear()
        if self.tileset_data:
            region_ids = ["obstacle_rock", "obstacle_crate", "obstacle_spike"]
            margin = 80
            cols = 4
            rows = 3
            cell_w = (self.SCREEN_WIDTH - 2 * margin) // cols
            cell_h = (self.SCREEN_HEIGHT - 2 * margin) // rows
            for i in range(self.OBSTACLE_COUNT):
                col = i % cols
                row = i // cols
                ox = margin + col * cell_w + random.randint(0, cell_w // 2)
                oy = margin + row * cell_h + random.randint(0, cell_h // 2)
                region_id = region_ids[i % len(region_ids)]
                region = self.tileset_data.get_region(region_id)
                if region:
                    obs = TilesetObstacle(region, ox, oy)
                    self.obstacles.append(obs)
                    self.manager.add_object(obs)

        # Count shapes
        circles = sum(1 for o in self.objects if isinstance(o, Ball) and not o.ghost)
        rects = sum(1 for o in self.objects if isinstance(o, Block))
        polys = sum(1 for o in self.objects if isinstance(o, Diamond))
        print(f"Reset: {circles} circles, {rects} rects, {polys} polygons, "
              f"{len(self.walls)} walls, {len(self.obstacles)} obstacles")

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_g:
                    self.ghost_enabled = not self.ghost_enabled
                    self.reset()
                elif event.key == pygame.K_F1:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_F11:
                    self.FULLSCREEN = not self.FULLSCREEN
                    if self.FULLSCREEN:
                        flags = pygame.FULLSCREEN | pygame.SCALED
                        self.screen = pygame.display.set_mode(
                            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), flags)
                    else:
                        self.screen = pygame.display.set_mode(
                            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

    def update(self, dt):
        """Update positions and resolve collisions."""
        for obj in self.objects:
            obj.update(dt, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        hits = self.manager.check_all_collisions()

        for hit in hits:
            a = hit.object_a
            b = hit.object_b

            if getattr(a, "ghost", False) or getattr(b, "ghost", False):
                continue

            a_is_static = not hasattr(a, "vx")
            b_is_static = not hasattr(b, "vx")

            # Separate
            sep_x = hit.normal[0] * hit.depth * 0.5
            sep_y = hit.normal[1] * hit.depth * 0.5
            if not a_is_static:
                a.x -= sep_x
                a.y -= sep_y
            if not b_is_static:
                b.x += sep_x
                b.y += sep_y

            # Bounce — only apply to dynamic objects
            if not a_is_static:
                dot_a = a.vx * hit.normal[0] + a.vy * hit.normal[1]
                a.vx -= dot_a * hit.normal[0]
                a.vy -= dot_a * hit.normal[1]
            if not b_is_static:
                dot_b = b.vx * hit.normal[0] + b.vy * hit.normal[1]
                b.vx -= dot_b * hit.normal[0]
                b.vy -= dot_b * hit.normal[1]

        return hits

    def render(self, debug_hits=None):
        """Render the scene."""
        self.screen.fill((30, 30, 50))

        for wall in self.walls:
            wall.draw(self.screen)

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        for obj in self.objects:
            obj.draw(self.screen, debug_hits if self.show_debug else None)

        # Debug overlay
        if self.show_debug:
            font = pygame.font.Font(None, 20)
            collision_count = len(debug_hits) if debug_hits else 0
            circles = sum(1 for o in self.objects if isinstance(o, Ball) and not o.ghost)
            rects = sum(1 for o in self.objects if isinstance(o, Block))
            polys = sum(1 for o in self.objects if isinstance(o, Diamond))
            fps = self.clock.get_fps()
            total = len(self.objects) + len(self.obstacles) + len(self.walls)
            text = font.render(
                f"FPS: {fps:.0f}/60  Objects: {total}  "
                f"Collisions: {collision_count}  "
                f"Circles: {circles}  Rects: {rects}  Polygons: {polys}  "
                f"Obstacles: {len(self.obstacles)}  "
                f"Ghost: {'ON' if self.ghost_enabled else 'OFF'}",
                True, (200, 200, 200))
            self.screen.blit(text, (10, 10))

        # Controls
        font = pygame.font.Font(None, 18)
        controls = ["ESC: Quit  |  R: Reset  |  G: Toggle Ghost  |  F1: Debug  |  F11: Fullscreen"]
        y = self.SCREEN_HEIGHT - 25
        for line in controls:
            text = font.render(line, True, (150, 150, 180))
            self.screen.blit(text, (10, y))

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        print("\nMixed-Shape Object Collision Example")
        print("Controls: R=Reset, G=Toggle Ghost, F1=Debug, ESC=Quit\n")

        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            hits = self.update(dt)
            self.render(debug_hits=hits)

        pygame.quit()
        print("Example ended.")


def main():
    """Entry point."""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
