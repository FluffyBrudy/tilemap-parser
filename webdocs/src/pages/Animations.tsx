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
        <code>AnimationPlayer.update()</code> takes{" "}
        <strong>milliseconds</strong>, not seconds. Feed it{" "}
        <code>clock.tick(60)</code> directly.
      </p>

      <h2 id="loading">LOADING</h2>
      <p>
        <code>SpriteAnimationSet.load()</code> is the one-call entry point: it
        parses the animation JSON and loads the spritesheet image in one step.
        The JSON's <code>spritesheet_path</code> is resolved relative to the
        JSON file; pass <code>spritesheet_path=</code> to override it.
      </p>
      <p>
        Pass <code>render_scale=</code> to scale the sheet and its atlas grid (
        <code>tile_size</code>, <code>grid_offset</code>) in one step — handy
        for hi-res art rendered at a lower resolution or vice versa. The grid is
        pinned from the original sheet, so fractional scales with a nonzero{" "}
        <code>grid_offset</code> still address cells correctly. Scales that are
        not finite, not &gt; 0, or that produce zero-sized or non-fitting cells
        are rejected at load.
      </p>
      <CodeBlock
        title="loading.py"
        code={`from tilemap_parser import SpriteAnimationSet, AnimationPlayer

anim_set = SpriteAnimationSet.load("data/animations/player.json", render_scale=2.0)
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
        <code>animation_name</code> attribute <em>is</em> the switching API. Set
        it, then reset the clock to start the new clip from frame 0:
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
        <code>trim_transparent</code>, each frame is trimmed to its content. Use{" "}
        <code>get_content_bounds()</code> to ask where the visible pixels are,
        and anchor your blit against it:
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
        <code>AnimationPlayer</code> is pure math: no surfaces, no pygame state.
        Only <code>SpriteAnimationSet.load()</code> touches the renderer, and
        only because it must load the spritesheet.
      </Callout>

      <h2 id="object-animations">OBJECT ANIMATIONS</h2>
      <p>
        Objects on an object layer can carry a typed{" "}
        <code>ObjectAnimation</code> (internal dataclass) — frames cut from the
        object's tileset in a row-major grid (left-to-right, top-to-bottom).
        Required fields fail early at parse time; optional fields have defaults.
        Access <code>obj.animation</code> directly for the raw parsed data, or
        use <code>TilemapData.get_object_animation(obj)</code> which returns
        normalized <code>AnimData</code> (a dict with <code>frames</code> as
        surfaces, <code>frame_w/h</code>, <code>frame_duration_ms</code>,{" "}
        <code>loop</code>, <code>animation_mode</code>, and{" "}
        <code>properties</code>).
      </p>
      <CodeBlock
        title="object animation json"
        code={`// inside data.layers[].objects[\"1\"]
{
  "area": {"x": 32, "y": 64, "w": 16, "h": 16},
  "ttype": 0,
  "tileset_type": "object",
  "variant": 0,
  "animation": {
    "frame_count": 4,          // Required
    "frame_duration_ms": 120,  // Required
    "speed": 1.0,
    "loop": true,
    "animation_mode": "default", // or "random_start_times"
    "random_phase": false,
    "frames": [0, 1, 2, 3]       // optional explicit order
  }
}`}
      />
      <CodeBlock
        title="object animation — python"
        code={`from tilemap_parser import load_map

data = load_map("data/map.json")
obj = data.get_layer("Objects").objects[1]

# Access raw parsed animation data from the object
raw_anim = obj.animation             # ObjectAnimation | None (internal dataclass)
if raw_anim is not None:
    print(raw_anim.frame_count, raw_anim.frame_duration_ms)

# get_object_animation returns normalized AnimData dict with frames + metadata
anim_data = data.get_object_animation(obj)  # AnimData | None
if anim_data is not None:
    frames = anim_data["frames"]             # list[Surface]
    print(anim_data["frame_duration_ms"], anim_data["loop"])
    print(anim_data["frame_w"], anim_data["frame_h"])
    # Draw current frame
    screen.blit(frames[frame_index], (obj.area.x, obj.area.y))`}
      />
      <ul>
        <li>
          <code>frame_count</code> and <code>frame_duration_ms</code> are
          required — missing or non-positive values raise{" "}
          <code>MapParseError</code>.
        </li>
        <li>
          <code>frames</code> overrides the default{" "}
          <code>0..frame_count-1</code> order when present.
        </li>
        <li>
          Frame slicing uses <code>obj.area.w × obj.area.h</code> (one frame) as
          the cell size across the object's tileset sheet.
        </li>
        <li>
          Access via <code>obj.animation.properties</code> is not needed — the
          dataclass is the typed view. Raw JSON stays on{" "}
          <code>data.parsed.raw</code>.
        </li>
      </ul>
      <Callout kind="info" title="PER-TILESET FALLBACK (SHARED STRIP)">
        Most maps store animation on the <code>tileset</code> (
        <code>resources.tilesets[].animation</code> — e.g., all coins share one
        5-frame strip) and leave per-object <code>animation</code> as{" "}
        <code>None</code> for efficiency.{" "}
        <code>TilemapData.get_object_animation(obj)</code> returns the effective
        animation (per-object if present, else{" "}
        <code>get_tileset_animation(obj.ttype)</code>).
      </Callout>
      <Callout kind="tip" title="RANDOM_START HASH (USER PLAYBACK)">
        When <code>animation_mode == "random_start_times"</code> desync
        deterministically via{" "}
        <code>
          (obj.area.x * 73856093 ^ obj.area.y * 19349663 ^ obj.ttype * 83492791)
          % count
        </code>
        , so identical potions don't tick in sync. Parser only gives{" "}
        <code>list[Surface]</code> + animation metadata (speed/loop); playback
        (elapsed * speed, loop clamp vs modulo) is user-side, like{" "}
        <code>TileLayerRenderer</code> does for tiles.
      </Callout>
    </div>
  );
}
