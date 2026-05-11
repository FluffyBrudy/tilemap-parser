"""
Animation Only Example
Load and play sprite animations using tilemap-parser
"""

import pygame
import sys
from pathlib import Path
from tilemap_parser import SpriteAnimationSet, AnimationPlayer

def main():
    # Initialize pygame
    pygame.init()
    
    # Screen setup
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("tilemap-parser - Animation Example")
    clock = pygame.time.Clock()
    target_fps = 60
    
    # Load sprite animation set
    anim_set = SpriteAnimationSet.load("data/RACCOONSPRITESHEET.anim.json")
    print(f"Loaded animation set with {len(anim_set.library.animations)} animations")
    
    # Create animation player for a specific animation
    # Available animations: idledown, idleright, idleup, idleleft
    anim_player = AnimationPlayer(anim_set, "idledown")
    
    # Main loop
    running = True
    while running:
        # Calculate delta time
        dt = clock.tick(target_fps) / 1000.0  # seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Change animation with keys 1-4
                elif event.key == pygame.K_1:
                    anim_player = AnimationPlayer(anim_set, "idledown")
                elif event.key == pygame.K_2:
                    anim_player = AnimationPlayer(anim_set, "idleright")
                elif event.key == pygame.K_3:
                    anim_player = AnimationPlayer(anim_set, "idleup")
                elif event.key == pygame.K_4:
                    anim_player = AnimationPlayer(anim_set, "idleleft")
        
        # Update animation
        anim_player.update(dt * 1000)  # convert to milliseconds
        
        # Clear screen
        screen.fill((30, 30, 40))  # Dark blue-gray
        
        # Get current frame and draw it centered
        frame = anim_player.get_current_image()
        if frame:
            # Calculate position to center the frame
            x = (screen_width - frame.get_width()) // 2
            y = (screen_height - frame.get_height()) // 2
            screen.blit(frame, (x, y))
            
            # Draw animation info
            font = pygame.font.Font(None, 24)
            info_text = f"Animation: {anim_player.clip.name} | Frame: {anim_player.current_frame}/{anim_player.clip.frame_count}"
            text_surface = font.render(info_text, True, (200, 200, 200))
            screen.blit(text_surface, (10, 10))
            
            # Draw controls info
            controls = [
                "Controls:",
                "1-4: Change animation",
                "ESC: Quit"
            ]
            y_offset = screen_height - 60
            for line in controls:
                text_surface = font.render(line, True, (180, 180, 180))
                screen.blit(text_surface, (10, y_offset))
                y_offset += 20
        
        # Update display
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()