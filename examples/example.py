import pygame
import json
from pathlib import Path
from editor import Editor
from tilemap_parser.map_loader import load_map
from tilemap_parser.renderer import TileLayerRenderer
from tilemap_parser.collision import parse_tileset_collision, RectangleShape
from tilemap_parser.collision_runner import CollisionRunner, MovementMode


pygame.init()


class Player:
    """Simple player character with collision"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(width=8, height=8, offset=(0, 0))
        self.speed = 150
        self.color = (255, 100, 100)
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw player as a colored rectangle"""
        rect = pygame.Rect(
            self.x - camera_x,
            self.y - camera_y,
            self.collision_shape.width,
            self.collision_shape.height
        )
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)


def draw_collision_shapes(screen, tileset_collision, tile_map, tile_size, camera_x=0, camera_y=0):
    """Draw collision shapes for debugging"""
    for (tile_x, tile_y), tile_id in tile_map.items():
        if tileset_collision.has_collision(tile_id):
            world_x = tile_x * tile_size[0]
            world_y = tile_y * tile_size[1]
            shapes = tileset_collision.get_world_shapes(tile_id, world_x, world_y)
            
            for shape in shapes:
                if len(shape.vertices) >= 3:
                    points = [(vx - camera_x, vy - camera_y) for vx, vy in shape.vertices]
                    color = (0, 255, 0, 128) if shape.one_way else (255, 255, 0, 128)
                    pygame.draw.polygon(screen, color, points, 2)


def main():
    screen = pygame.display.set_mode((1200, 700))
    clock = pygame.time.Clock()
    script_dir = Path(__file__).parent
    map_path = script_dir / "collision.json"  # This is the actual map file
    collision_path = script_dir / "collision_data.json"

    # Load map and renderer
    parser = load_map(str(map_path))
    renderer = TileLayerRenderer(parser)
    renderer.warm_cache()
    
    # Load collision data directly from collision_data.json
    with open(collision_path, 'r') as f:
        collision_json = json.load(f)
    tileset_collision = parse_tileset_collision(collision_json)
    
    if not tileset_collision:
        print("Warning: No collision data loaded!")
        return
    
    # Build tile map for collision checking
    tile_map = {}
    for layer in parser.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant
    
    # Create collision runner with tile size from map (should match collision data)
    collision_runner = CollisionRunner(
        collision_cache=None,
        tile_size=parser.tile_size,
        mode=MovementMode.SLIDE
    )
    
    # Create player
    player = Player(100, 100)
    
    # Camera
    camera_x, camera_y = 0, 0
    
    # Debug mode
    show_collision = True
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    show_collision = not show_collision
        
        # Handle input
        keys = pygame.key.get_pressed()
        delta_x = 0
        delta_y = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            delta_x -= player.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            delta_x += player.speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            delta_y -= player.speed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            delta_y += player.speed * dt
        
        # Initialize result
        result = None
        
        # Move player with collision (with slope sliding enabled)
        if delta_x != 0 or delta_y != 0:
            result = collision_runner.move_and_slide(
                player,
                tileset_collision,
                tile_map,
                delta_x,
                delta_y,
                slope_slide=True  # Enable slope sliding
            )
            
            # Visual feedback on collision
            if result.collided:
                player.color = (255, 50, 50)
            else:
                player.color = (100, 255, 100)
        else:
            # Reset color when not moving
            player.color = (100, 200, 255)
        
        # Update camera to follow player
        camera_x = player.x - 600 + 8
        camera_y = player.y - 350 + 8
        
        # Render
        screen.fill((50, 50, 80))
        renderer.render(screen, camera_xy=(camera_x, camera_y))
        
        # Draw collision shapes
        if show_collision:
            draw_collision_shapes(screen, tileset_collision, tile_map, parser.tile_size, camera_x, camera_y)
        
        # Draw player
        player.draw(screen, camera_x, camera_y)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "Arrow Keys / WASD: Move",
            "C: Toggle collision visualization",
            f"Position: ({int(player.x)}, {int(player.y)})",
            f"Collision: {'YES' if result and result.collided else 'NO'}"
        ]
        for i, text in enumerate(instructions):
            surf = font.render(text, True, (255, 255, 255))
            screen.blit(surf, (10, 10 + i * 25))
        
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
