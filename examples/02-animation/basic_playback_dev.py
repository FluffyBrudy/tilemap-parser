"""
Animation Playback - Development Mode

USAGE: Run this script from the repository root with the local source.

    python examples/02-animation/basic_playback_dev.py
"""

import sys
from pathlib import Path

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tilemap_parser import SpriteAnimationSet, AnimationPlayer


def main():
    # Path to animation JSON (adjust as needed)
    script_dir = Path(__file__).parent
    anim_path = script_dir.parent.parent / "examples" / "hero.anim.json"
    
    if not anim_path.exists():
        print(f"Animation file not found: {anim_path}")
        return
    
    # Load animation set
    # spritesheet_path is resolved relative to the JSON file
    anim_set = SpriteAnimationSet.load(str(anim_path))
    
    # Access animation library
    library = anim_set.library
    print(f"Available animations: {list(library.animations.keys())}")
    
    # Get a specific animation clip
    idle_clip = library.get("idle")
    if idle_clip:
        print(f"\nIdle animation:")
        print(f"  Frames: {idle_clip.frame_count()}")
        print(f"  Duration: {idle_clip.total_duration_ms():.0f}ms")
        print(f"  Loops: {idle_clip.loop}")
    
    # Create a player for the "idle" animation
    player = AnimationPlayer(anim_set, "idle")
    
    print("\nPlaying idle animation for 500ms...")
    
    # Simulate game loop - update every ~16.67ms (60fps)
    total_time = 500  # 500ms
    dt = 16.67  # ~60fps
    
    while not player.finished:
        player.update(dt)
        frame = player.get_current_image()
        if frame:
            print(f"  Frame {player.frame_index}: {frame.get_size()}")
        if player._elapsed_in_frame >= dt * 10:
            break  # Safety limit for demo
    
    # Reset and play again
    player.reset()
    print("\nReset and replaying...")


if __name__ == "__main__":
    main()