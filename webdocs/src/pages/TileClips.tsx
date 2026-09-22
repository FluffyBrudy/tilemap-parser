import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function TileClips() {
  return (
    <div className="content">
      <h1>Tile Clips: sidecar animations for tiles</h1>
      <p>
        Stride animation moves a whole tileset (<code>variant + frame × stride</code>).
        Tile clips animate <em>individual cells</em>: the editor authors named,
        ordered, multi-sheet clips into <code>*.tanim.json</code> sidecars, assigns
        them per variant with the <code>anim_clip</code> tile property, and{" "}
        <code>TileLayerRenderer</code> plays them. Stride behavior is unchanged.
      </p>

      <h2 id="sidecar">SIDECAR FORMAT</h2>
      <CodeBlock
        title="water.tanim.json"
        code={`{"version": 1, "tileset": "tiles/water.png",
 "clips": {"waves": {"loop": true, "mode": "default",
   "frames": [{"sheet": "tiles/water.png", "variant": 5, "duration_ms": 120.0}]}}}`}
      />
      <ul>
        <li>
          Frames are <strong>ordered</strong> with per-frame{" "}
          <code>duration_ms</code>; sheets are path refs resolved against loaded
          tilesets (exact path first, unique basename/stem fallback).
        </li>
        <li>
          Assignment lives in the map JSON (
          <code>tile_properties[variant]["anim_clip"] = "waves"</code>); the
          sidecar holds reusable definitions only.
        </li>
        <li>
          Malformed leaves are skipped; bad files load as empty. A file can never
          break rendering.
        </li>
      </ul>

      <h2 id="loading">LOADING</h2>
      <CodeBlock
        title="clips.py"
        code={`from tilemap_parser import TileLayerRenderer, load_tile_anim_file, find_tileanims

renderer = TileLayerRenderer(data, tile_clips="data/tileanims/water.tanim.json")
renderer = TileLayerRenderer(data, tile_clips=["a.tanim.json", "b.tanim.json"])
renderer = TileLayerRenderer(data, tile_clips={"waves": clip})  # pre-parsed
renderer = TileLayerRenderer(data)  # legacy: stride/static, byte-identical

auto = find_tileanims("data/tileanims")  # sorted sidecar paths`}
      />
      <p>
        <code>clip_property</code> (default <code>"anim_clip"</code>) names the tile
        property key; effective properties merge tileset{" "}
        <code>tile_properties[variant]</code> under per-placement props.{" "}
        <code>load_optional_anim="anim"</code> restricts stride animation to flagged
        tiles. Duplicate clip names: first loaded wins, with a warning on{" "}
        <code>renderer.warnings</code>.
      </p>

      <h2 id="precedence">PRECEDENCE PER CELL</h2>
      <p>
        <strong>clip &gt; flagged stride &gt; tileset stride &gt; static.</strong>{" "}
        An explicit clip assignment always beats the blanket; nothing assigned
        behaves exactly as before.
      </p>

      <h2 id="fallback">FALLBACK BEHAVIOR</h2>
      <p>
        Animation only ever replaces the blit. Whatever was plotted always renders:
      </p>
      <ul>
        <li>Unknown clip name, empty clip, unresolvable sheets → base variant.</li>
        <li>Out-of-range frame → base variant for that frame, never a hole.</li>
        <li>Non-looping clip past its end → holds the last frame.</li>
      </ul>
      <Callout kind="warn" title="PLOTTED TILE ALWAYS RENDERS">
        A broken clip degrades to the static base variant — not to stride. The
        assignment opts the tile out of the blanket.
      </Callout>

      <h2 id="timing">TIMING AND PHASE</h2>
      <p>
        Frame lookup walks cumulative durations (same rule as the editor's{" "}
        <code>clip_frame_at</code>). <code>mode: "random_start_times"</code>{" "}
        rotates the frame order per cell with the standard hash (
        <code>(x * 73856093 ^ y * 19349663 ^ ttype * 83492791) % len(frames)</code>
        ), so identical cells don't tick in sync.
      </p>
      <CodeBlock
        title="timing.py"
        code={`from tilemap_parser import clip_frame_at

frame = clip_frame_at(clip, pygame.time.get_ticks())  # pure function, no renderer needed`}
      />
    </div>
  );
}
