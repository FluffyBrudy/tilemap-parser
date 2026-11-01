import Callout from "../components/Callout";
import CodeBlock from "../components/CodeBlock";
import Toc, { type TocItem } from "../components/Toc";

const TOC: TocItem[] = [
  { id: "data", label: "ObjectAnimation Data Access" },
  { id: "json", label: "JSON Schema & Object Properties" },
  { id: "playback", label: "Playback via get_object_animation" },
  { id: "fallback", label: "Tileset Animation Fallback" },
  { id: "random", label: "Desynchronized Playback (random_start_times)" },
];

export default function AnimationObjects() {
  return (
    <div className="content">
      <h1>Object Animations: Map-Placed Dynamic Objects</h1>
      <p>
        Objects on an object layer can carry a typed{" "}
        <code>ObjectAnimation</code> (internal dataclass) — frames cut from the
        object's tileset in a row-major grid (left-to-right, top-to-bottom).
        Required fields fail early at parse time; optional fields have
        defaults. For sprite-sheet clip playback instead, see{" "}
        <a href="/animations">Animation Basics</a>; for per-cell tile
        animations, see <a href="/animations/tile-clips">Tile Clips</a>.
      </p>
      <Toc items={TOC} />

      <h2 id="data">ObjectAnimation Data Access</h2>
      <p>
        Access <code>obj.animation</code> directly for the raw parsed data, or
        use <code>TilemapData.get_object_animation(obj)</code>, which returns
        normalized <code>AnimData</code>: a dict with <code>frames</code> as
        surfaces, <code>frame_w/h</code>, <code>frame_duration_ms</code>,{" "}
        <code>loop</code>, <code>animation_mode</code>, and{" "}
        <code>properties</code>.
      </p>
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
          Frame slicing uses <code>obj.area.w × obj.area.h</code> (one frame)
          as the cell size across the object's tileset sheet.
        </li>
        <li>
          Access via <code>obj.animation.properties</code> is not needed — the
          dataclass is the typed view. Raw JSON stays on{" "}
          <code>data.parsed.raw</code>.
        </li>
      </ul>

      <h2 id="json">JSON Schema &amp; Object Properties</h2>
      <CodeBlock
        title="object animation json"
        code={`// inside data.layers[].objects["1"]
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

      <h2 id="playback">Playback via get_object_animation</h2>
      <CodeBlock
        title="object animation — python"
        code={`from tilemap_parser import load_map

data = load_map("data/map.json")
obj = data.get_layer("Objects").objects[1]   # dict: key == object id

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
      <Callout kind="info" title="PROPERTIES TRAVEL ON ANIMDATA">
        <code>anim_data[&quot;properties&quot;]</code> carries {" "}the object's{" "}
        <code>obj.properties</code> copy, so gameplay hooks can be read from
        the same dict the frames arrive in.
      </Callout>

      <h2 id="fallback">Tileset Animation Fallback (Shared Strip)</h2>
      <Callout kind="info" title="SHARED STRIP">
        Most maps store animation on the <code>tileset</code> (
        <code>resources.tilesets[].animation</code> — e.g., all coins share one
        5-frame strip) and leave per-object <code>animation</code> as{" "}
        <code>None</code> for efficiency.{" "}
        <code>TilemapData.get_object_animation(obj)</code> returns the
        effective animation (per-object if present, else{" "}
        <code>get_tileset_animation(obj.ttype)</code>).
      </Callout>

      <h2 id="random">Desynchronized Playback (random_start_times)</h2>
      <Callout kind="tip" title="DETERMINISTIC PHASE HASH">
        When <code>animation_mode == &quot;random_start_times&quot;</code>,
        desync placements deterministically via{" "}
        <code>
          (obj.area.x * 73856093 ^ obj.area.y * 19349663 ^ obj.ttype *
          83492791) % count
        </code>
        , so identical placements do not tick in sync. The parser only gives{" "}
        <code>list[Surface]</code> plus animation metadata (speed/loop);
        playback (elapsed × speed, loop clamp vs modulo) is user-side, like{" "}
        <code>TileLayerRenderer</code> does for tiles.
      </Callout>
    </div>
  );
}
