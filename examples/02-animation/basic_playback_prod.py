"""
Animation Playback - Production Mode

USAGE: Run with tilemap-parser installed from PyPI.

    pip install tilemap-parser
    python examples/02-animation/basic_playback_prod.py
"""

from tilemap_parser import SpriteAnimationSet, AnimationPlayer


def main():
    # Load animation - spritesheet_path is resolved relative to JSON file
    anim_path = "assets/anims/hero.anim.json"
    anim_set = SpriteAnimationSet.load(anim_path)
    
    # List all available animations
    print("Available animations:")
    for name in anim_set.library.animations:
        print(f"  - {name}")
    
    # Create player for a specific animation
    player = AnimationPlayer(anim_set, "idle")
    
    # Check animation properties
    clip = player.clip
    if clip:
        print(f"\nPlaying: {clip.name}")
        print(f"  Total frames: {clip.frame_count()}")
        print(f"  Duration: {clip.total_duration_ms():.0f}ms")
        
        # Check markers
        if clip.markers:
            print(f"  Markers: {[m.name for m in clip.markers]}")
    
    # Game loop simulation
    print("\n--- Game Loop Simulation ---")
    dt = 16.67  # 60fps
    
    for frame_num in range(10):
        player.update(dt)
        surface = player.get_current_image()
        status = "playing" if not player.finished else "finished"
        print(f"Frame {frame_num}: index={player.frame_index}, status={status}")
    
    # Switch animation at runtime
    print("\n--- Switching to 'walk' animation ---")
    player.animation_name = "walk"
    player.reset()
    
    for frame_num in range(5):
        player.update(dt)
        surface = player.get_current_image()
        print(f"Frame {frame_num}: index={player.frame_index}")


if __name__ == "__main__":
    main()