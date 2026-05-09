"""
Complete game example demonstrating tilemap-parser features:
- Map loading and rendering with TileLayerRenderer
- Collision detection with CollisionRunner
- Player movement with collision response
- Sprite animation with AnimationPlayer

Controls:
- Arrow keys or WASD: Move player
- ESC: Quit game
"""

import pygame
import sys
from pathlib import Path
from tilemap_parser import (
    load_map, 
    SpriteAnimationSet, 
    AnimationPlayer, 
    TileLayerRenderer, 
    CollisionRunner, 
    CollisionCache,
    RectangleShape
)


class Player:
    """
    Player class implementing the ICollidableSprite protocol.
    
    Required attributes for collision system:
    - x, y: World position (float)
    - collision_shape: Shape for collision detection
    - vx, vy: Velocity (for physics-based modes)
    - on_ground: Ground state (for platformer mode)
    """
    
    def __init__(self, x, y, animation_set):
        self.x = float(x)
        self.y = float(y)
        
        # Collision shape: 12x12 rectangle with offset to center it on sprite
        # The offset positions the collision box relative to (x, y)
        self.collision_shape = RectangleShape(12, 12, offset=(-6, -6))
        
        # Animation system
        self.animation_set = animation_set
        self.animation_player = AnimationPlayer(animation_set, "idledown")
        self.facing = "down"
        self.is_moving = False
        
        # Velocity (required by ICollidableSprite protocol)
        self._vx = 0.0
        self._vy = 0.0
        
    @property
    def vx(self):
        return self._vx
    
    @vx.setter
    def vx(self, value):
        self._vx = value
        
    @property
    def vy(self):
        return self._vy
    
    @vy.setter
    def vy(self, value):
        self._vy = value
        
    @property
    def on_ground(self):
        # Not used in top-down mode, but required for protocol
        return False
    
    def update_animation(self, dt):
        """Update animation based on movement state"""
        # Determine animation name
        if self.is_moving:
            # Note: The animation file uses "idledown", "idleright", etc.
            # In a real game, you'd have separate walk animations
            anim_name = f"idle{self.facing}"
        else:
            anim_name = f"idle{self.facing}"
        
        # Update animation player if animation changed
        current_clip = self.animation_player.clip
        if current_clip is None or current_clip.name != anim_name:
            self.animation_player = AnimationPlayer(self.animation_set, anim_name)
        
        # Update animation frame
        self.animation_player.update(dt * 1000)  # Convert seconds to milliseconds
    
    def render(self, surface, camera_x, camera_y):
        """Render player sprite and collision box (for debugging)"""
        # Get current animation frame
        frame = self.animation_player.get_current_image()
        if frame:
            # Calculate screen position (center sprite on player position)
            screen_x = self.x - camera_x - frame.get_width() // 2
            screen_y = self.y - camera_y - frame.get_height() // 2
            surface.blit(frame, (screen_x, screen_y))
            
            # Draw collision box for debugging (red rectangle)
            bounds = self.collision_shape.get_bounds(self.x, self.y)
            debug_rect = pygame.Rect(
                bounds[0] - camera_x,
                bounds[1] - camera_y,
                bounds[2] - bounds[0],
                bounds[3] - bounds[1]
            )
            pygame.draw.rect(surface, (255, 0, 0), debug_rect, 1)

class Game:
    """Main game class managing all game systems"""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Screen setup
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Tilemap-Parser Game Example")
        self.clock = pygame.time.Clock()
        self.target_fps = 60
        
        # Load game data
        print("Loading game data...")
        self.load_game_data()
        
        # Game state
        self.running = True
        self.show_debug = True  # Toggle with F1
        
    def load_game_data(self):
        """Load all game resources"""
        # Load map
        self.game_data = load_map("data/map.json")
        print(f"Map loaded: {self.game_data.tile_size} tile size")
        
        # Load player animations
        self.player_anim_set = SpriteAnimationSet.load("data/RACCOONSPRITESHEET.anim.json")
        print(f"Player animations loaded: {len(self.player_anim_set.library.animations)} animations")
        
        # Setup renderer
        self.renderer = TileLayerRenderer(self.game_data)
        # Note: We don't call warm_cache() because it sets data=None which breaks rendering
        # The renderer will cache tiles on-demand during rendering
        print("Renderer initialized")
        
        # Setup collision system
        self.collision_cache = CollisionCache()
        self.tileset_collision = self.collision_cache.get_tileset_collision(
            "data/collision/HiddenJungle_PNG.collision.json"
        )
        
        if self.tileset_collision:
            collision_count = len([t for t in self.tileset_collision.tiles.values() if t.has_collision()])
            print(f"Collision data loaded: {collision_count} tiles with collision")
        else:
            print("Warning: No collision data loaded!")
        
        # Create collision runner for top-down movement
        self.collision_runner = CollisionRunner.from_game_type(
            'topdown', 
            self.collision_cache, 
            self.game_data.tile_size
        )
        print("Collision runner initialized for top-down movement")
        
        # Build tile map for collision detection
        # Maps (tile_x, tile_y) -> tile_variant_id
        self.tile_map = {}
        for layer in self.game_data.parsed.layers:
            if layer.layer_type == "tile":
                for (tile_x, tile_y), tile in layer.tiles.items():
                    # Store the tile variant (which maps to collision data)
                    if isinstance(tile.ttype, int):
                        self.tile_map[(tile_x, tile_y)] = tile.variant
        
        print(f"Tile map built: {len(self.tile_map)} tiles")
        
        # Create player at starting position (in an open area without collision)
        # Start at tile (5, 7) which has no collision
        start_x = 5.5 * self.game_data.tile_size[0]  # Center of tile
        start_y = 7.5 * self.game_data.tile_size[1]  # Center of tile
        self.player = Player(start_x, start_y, self.player_anim_set)
        print(f"Player created at ({start_x}, {start_y})")
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F1:
                    self.show_debug = not self.show_debug
    
    def update(self, dt):
        """Update game state"""
        # Get input
        keys = pygame.key.get_pressed()
        input_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        input_y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        
        # Normalize diagonal movement
        if input_x != 0 and input_y != 0:
            input_x *= 0.7071  # 1/sqrt(2)
            input_y *= 0.7071
        
        # Update player facing direction
        self.player.is_moving = (input_x != 0 or input_y != 0)
        if self.player.is_moving:
            if abs(input_x) > abs(input_y):
                self.player.facing = "right" if input_x > 0 else "left"
            else:
                self.player.facing = "down" if input_y > 0 else "up"
        
        # Apply movement with collision
        speed = 100.0  # pixels per second
        delta_x = input_x * speed * dt
        delta_y = input_y * speed * dt
        
        if delta_x != 0 or delta_y != 0:
            # Move player with collision detection
            result = self.collision_runner.move_and_slide(
                self.player,
                self.tileset_collision,
                self.tile_map,
                delta_x,
                delta_y,
                slope_slide=True  # Enable smooth sliding along walls
            )
        
        # Update player animation
        self.player.update_animation(dt)
    
    def render(self):
        """Render game"""
        # Clear screen
        self.screen.fill((50, 50, 80))  # Dark blue background
        
        # Calculate camera position (center on player)
        camera_x = self.player.x - self.screen_width // 2
        camera_y = self.player.y - self.screen_height // 2
        
        # Render tilemap
        self.renderer.render(self.screen, camera_xy=(camera_x, camera_y))
        
        # Render player
        self.player.render(self.screen, camera_x, camera_y)
        
        # Render debug info
        if self.show_debug:
            self.render_debug_info()
        
        # Update display
        pygame.display.flip()
    
    def render_debug_info(self):
        """Render debug information overlay"""
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        # FPS
        fps = int(self.clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
        self.screen.blit(fps_text, (10, 10))
        
        # Player position
        pos_text = small_font.render(
            f"Position: ({int(self.player.x)}, {int(self.player.y)})", 
            True, (255, 255, 255)
        )
        self.screen.blit(pos_text, (10, 35))
        
        # Tile position
        tile_x = int(self.player.x // self.game_data.tile_size[0])
        tile_y = int(self.player.y // self.game_data.tile_size[1])
        tile_text = small_font.render(
            f"Tile: ({tile_x}, {tile_y})", 
            True, (255, 255, 255)
        )
        self.screen.blit(tile_text, (10, 55))
        
        # Controls
        controls = [
            "Controls:",
            "WASD/Arrows - Move",
            "F1 - Toggle Debug",
            "ESC - Quit"
        ]
        y_offset = self.screen_height - 90
        for line in controls:
            text = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (10, y_offset))
            y_offset += 20
    
    def run(self):
        """Main game loop"""
        print("\nGame started!")
        print("Controls: WASD or Arrow keys to move, F1 for debug, ESC to quit\n")
        
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(self.target_fps) / 1000.0
            
            # Game loop
            self.handle_events()
            self.update(dt)
            self.render()
        
        # Cleanup
        pygame.quit()
        print("Game ended.")


def main():
    """Entry point"""
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
