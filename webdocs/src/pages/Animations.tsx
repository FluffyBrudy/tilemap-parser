import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function Animations() {
  return (
    <div className="content">
      <h1>Animations: frame-based sprites</h1>
      <p>
        The animation system is two objects and one rule.{" "}
        <code>SpriteAnimationSet</code> holds the parsed clips and the loaded
        spritesheet; <code>AnimationPlayer</code> is a pure frame clock that
        advances clip time and hands you the right frame image. The rule:
        <code>AnimationPlayer.update()</code> takes <strong>milliseconds</strong>
        , not seconds. Feed it <code>clock.tick(60)</code> directly.
      </p>

      <h2 id="loading">LOADING</h2>
      <p>
        <code>SpriteAnimationSet.load()</code> is the one-call entry point: it
        parses the animation JSON and loads the spritesheet image in one step.
        The JSON's <code>spritesheet_path</code> is resolved relative to the
        JSON file; pass <code>spritesheet_path=</code> to override it.
      </p>
      <CodeBlock
        title="loading.py"
        code={`from tilemap_parser import SpriteAnimationSet, AnimationPlayer

anim_set = SpriteAnimationSet.load("data/animations/player.json")
# anim_set.warnings collects non-fatal issues from the JSON

player = AnimationPlayer(anim_set, "idle")   # animation_name is REQUIRED`}
      />
      <p>
        If you already have the JSON loaded separately,{" "}
        <code>parse_animation_file(path)</code> (or{" "}
        <code>parse_animation_dict</code> / <code>parse_animation_json</code>)
        returns the <code>AnimationLibrary</code>: the parsed clips,{" "}
        <code>spritesheet_path</code>, <code>tile_size</code> and{" "}
        <code>grid_offset</code>. Bad files raise{" "}
        <code>AnimationParseError</code>.
      </p>

      <h2 id="playback">PLAYBACK: ONE CALL PER FRAME</h2>
      <p>
        Advance the clock, grab the frame image, draw it. The player owns no
        position. You decide where to blit.
      </p>
      <CodeBlock
        title="game loop"
        code={`dt_ms = clock.tick(60)      # pygame returns MILLISECONDS
player.update(dt_ms)

image = player.get_current_image()   # Surface | None
if image is not None:
    screen.blit(image, (player_x, player_y))`}
      />
      <ul>
        <li>
          <code>frame_index</code>: current frame position (int).
        </li>
        <li>
          <code>finished</code>: True when a non-looping clip has played out;
          <code>update()</code> then no-ops until <code>reset()</code>.
        </li>
        <li>
          <code>clip</code>: the current <code>AnimationClip</code> (or{" "}
          <code>None</code> if the name isn't in the library).
        </li>
        <li>
          <code>reset()</code>: back to frame 0 of the current clip.
        </li>
      </ul>
      <Callout kind="warn" title="DT IS MILLISECONDS">
        <code>update()</code> expects milliseconds because the JSON stores{" "}
        <code>duration_ms</code> per frame. Passing seconds makes clips run
        ~1000× too fast, the most common animation bug in this library.
      </Callout>

      <h2 id="switching">SWITCHING ANIMATIONS</h2>
      <p>
        There is no <code>play()</code> method. The player's{" "}
        <code>animation_name</code> attribute <em>is</em> the switching API.
        Set it, then reset the clock to start the new clip from frame 0:
      </p>
      <CodeBlock
        title="state.py"
        code={`target = "run" if moving else "idle"
if player.animation_name != target:
    player.animation_name = target
    player.reset()     # restart the new clip at frame 0`}
      />
      <p>
        Each <code>AnimationClip</code> declares its frames, per-frame{" "}
        <code>duration_ms</code>, <code>loop</code>, <code>fps</code> and
        metadata. Clips repeat by looping; for an attack you restart the same
        clip with <code>reset()</code>.
      </p>

      <h2 id="anchoring">ANCHORING AND PIXEL-PERFECT DRAW</h2>
      <p>
        Frames are cut from the spritesheet on a grid, honoring the library's{" "}
        <code>tile_size</code> and <code>grid_offset</code>. If the JSON enables{" "}
        <code>trim_transparent</code>, each frame is trimmed to its content.
        Use <code>get_content_bounds()</code> to ask where the visible pixels
        are, and anchor your blit against it:
      </p>
      <CodeBlock
        title="anchor.py"
        code={`bounds = anim_set.get_content_bounds(player.animation_name)
if bounds is not None:
    image = player.get_current_image()
    if image is not None:
        screen.blit(image, (x - bounds.x, y - bounds.y))   # keep feet planted`}
      />

      <h2 id="markers">MARKERS ARE DATA, NOT CALLBACKS</h2>
      <p>
        Clips can carry named <code>AnimationMarker</code>s (e.g. "hit",
        "footstep") at frame indexes. The player exposes them on{" "}
        <code>clip.markers</code>. There is no built-in callback; you do the
        frame-crossing check yourself:
      </p>
      <CodeBlock
        title="markers.py"
        code={`prev_frame = 0  # keep this across frames

clip = player.clip
if clip is not None:
    f = player.frame_index
    if f >= prev_frame:
        crossed = set(range(prev_frame + 1, f + 1))
    else:
        # looped: finish the old run, then frames 0..f of the new one
        crossed = set(range(prev_frame + 1, clip.frame_count())) | set(range(0, f + 1))
    for m in clip.markers:
        if m.name == "hit" and m.frame_index in crossed:
            apply_damage()
    prev_frame = f`}
      />

      <Callout kind="info" title="HEADLESS-FRIENDLY">
        <code>AnimationPlayer</code> is pure math: no surfaces, no pygame
        state. Only <code>SpriteAnimationSet.load()</code> touches the
        renderer, and only because it must load the spritesheet.
      </Callout>
    </div>
  );
}
