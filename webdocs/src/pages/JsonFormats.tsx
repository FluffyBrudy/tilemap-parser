import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

const MAP = `{
  "meta": {
    "tile_size": "32;32",
    "map_size": "30;20",
    "zoom_level": 1.0,
    "render_scale": 1.0,
    "version": "1.1"
  },
  "resources": { "tilesets": [] },
  "project_state": { "rules": [], "groups": [], "automap_rules": [] },
  "data": {
    "ongrid": {},
    "layers": [
      {
        "name": "Layer 1",
        "type": "tile",
        "visible": true,
        "locked": false,
        "opacity": 1.0,
        "z_index": 0,
        "tiles": {},
        "properties": {}
      }
    ]
  }
}`;

const TILESET = `{
  "tileset_name": "Terrain (32x32)",
  "tile_size": [32, 32],
  "tiles": {
    "8": {
      "tile_id": 8,
      "shapes": [
        { "type": "polygon", "vertices": [[0.0, 16.0], [32.0, 16.0], [32.0, 32.0], [0.0, 32.0]], "one_way": true }
      ]
    },
    "26": {
      "tile_id": 26,
      "shapes": [
        { "type": "polygon", "vertices": [[0.0, 0.0], [32.0, 0.0], [32.0, 32.0], [0.0, 32.0]], "one_way": false }
      ]
    }
  }
}`;

const CHARACTER = `{
  "name": "hero",
  "shape": {
    "type": "rectangle",
    "width": 24.0,
    "height": 32.0,
    "offset": [4.0, 0.0]
  },
  "properties": {
    "collision_layer": 1,
    "collision_mask": 65535
  }
}`;

const ANIM = `{
  "spritesheet_path": "../../assets/player_spritesheet.png",
  "tile_size": [128, 96],
  "grid_offset": [0, 0],
  "animations": {
    "idle": {
      "name": "idle",
      "frames": [
        { "variant_id": 0, "duration_ms": 100.0 },
        { "variant_id": 1, "duration_ms": 100.0 }
      ],
      "loop": true,
      "fps": 60.0
    },
    "jump": {
      "name": "jump",
      "frames": [ { "variant_id": 30, "duration_ms": 100.0 } ],
      "loop": false,
      "fps": 60.0
    }
  }
}`;

const NODE = `{
  "version": 1,
  "groups": [],
  "nodes": [
    {
      "node_id": "fc5eae05-0f8b-42f2-9b5e-9f1d0fa1752d",
      "name": "Emitter 1",
      "node_type": "particle_emitter",
      "area": { "x": 90, "y": 5, "w": 485, "h": 314 },
      "layer_name": "decoration",
      "properties": {
        "emission_shape": "rect",
        "particle_shape": "circle",
        "particle_size_min": 1,
        "particle_size_max": 3,
        "spawn_rate": 60,
        "max_particles": 180,
        "lifetime_min": 1.0,
        "lifetime_max": 3.0,
        "speed_min": 50,
        "speed_max": 120,
        "direction": 0,
        "spread": 15,
        "gravity_x": 80,
        "gravity_y": 5,
        "start_color_r": 200, "start_color_g": 180, "start_color_b": 140, "start_color_a": 180,
        "end_color_r": 160, "end_color_g": 140, "end_color_b": 100, "end_color_a": 20,
        "start_scale": 1.0,
        "end_scale": 0.5,
        "rotation_speed": 5,
        "alpha_fade": "fade_out"
      },
      "group": null
    }
  ]
}`;

export default function JsonFormats() {
  return (
    <div className="content">
      <h1>JSON Formats</h1>
      <p>
        Everything below is real data from the examples and fixtures, nothing
        invented. Each format shows the file and what the parser exposes from
        it. Files are authored in{" "}
        <a href="https://pypi.org/project/tilemap-editor/">tilemap-editor</a>;
        hand-writing them is possible but the editor keeps them consistent.
      </p>

      <h2 id="map">TILEMAP MAP</h2>
      <CodeBlock title="map.json" language="json" code={MAP} />
      <ul>
        <li>
          <code>meta</code>: <code>tile_size</code> (semicolon-delimited),{" "}
          <code>map_size</code>, <code>render_scale</code>, version. Exposed as{" "}
          <code>TilemapData.parsed.meta</code> and <code>tile_size</code>/
          <code>render_scale</code>.
        </li>
        <li>
          <code>resources.tilesets</code>: tileset references, incl. animation
          metadata for animated tiles.
        </li>
        <li>
          <code>data.layers</code>: tile layers with visibility,{" "}
          <code>z_index</code>, opacity, per-tile entries.
        </li>
        <li>
          Parser entry: <code>load_map(path)</code> → <code>TilemapData</code>;{" "}
          <code>build_tile_map()</code> flattens layers into the collision dict.
        </li>
      </ul>

      <h2 id="tileset">TILESET COLLISION</h2>
      <CodeBlock title="terrain.collision.json" language="json" code={TILESET} />
      <ul>
        <li>
          Top-level <code>tileset_name</code> + <code>tile_size</code>; per-id{" "}
          <code>tiles</code> with <code>shapes[]</code>.
        </li>
        <li>
          Each shape: <code>type: "polygon"</code>, <code>vertices</code>{" "}
          (tile-local, y-down), <code>one_way</code>.
        </li>
        <li>
          Tiles missing from <code>tiles</code> are walkable. Tile{" "}
          <code>8</code> above is a one-way platform (top 16px solid).
        </li>
        <li>
          Parser: <code>parse_tileset_collision</code> /{" "}
          <code>load_tileset_collision</code> /{" "}
          <code>CollisionCache.get_tileset_collision</code> →{" "}
          <code>TilesetCollision</code>.
        </li>
      </ul>

      <h2 id="character">CHARACTER COLLISION</h2>
      <CodeBlock title="hero.collision.json" language="json" code={CHARACTER} />
      <ul>
        <li>
          One <code>shape</code> per character: <code>rectangle</code> |{" "}
          <code>circle</code> | <code>capsule</code> | <code>polygon</code>,
          with <code>offset</code>.
        </li>
        <li>
          <code>properties.collision_layer</code> / <code>collision_mask</code>{" "}
          default to 1 / all.
        </li>
        <li>
          Parser: <code>parse_character_collision</code> /{" "}
          <code>load_character_collision</code> →{" "}
          <code>CharacterCollision</code>. Apply its <code>shape</code> to your
          sprite at spawn. Both accept <code>render_scale=</code> to scale the
          shape's dimensions and offsets. By design this scales collision data
          only — no image is touched — so the sprite paired with the shape must
          already be at the target resolution (e.g. frames from{" "}
          <code>SpriteAnimationSet.load(render_scale=...)</code>).
        </li>
      </ul>
      <Callout kind="tip" title="KEEPING SHAPE + SPRITE IN SYNC">
        Define the shape on the same spritesheet your animation uses, then pass
        the same <code>render_scale</code> to both{" "}
        <code>SpriteAnimationSet.load()</code> and the character collision load.
        Both are derived from the same source with the same scale factor, so the
        shape auto-syncs with the scaled frames — no hand-scaled image, no
        double work.
      </Callout>

      <h2 id="object">OBJECT COLLISION</h2>
      <p>
        Region-based polygon paint:{" "}
        <code>{`tileset_name, regions: { id: { name, region_rect, shapes[], properties } }`}</code>
        . Parsed by <code>parse_object_collision</code> →{" "}
        <code>ObjectCollisionData</code> with <code>get_region(region_id)</code>
        . Each region carries its own layer/mask.
      </p>

      <h2 id="animation">ANIMATION</h2>
      <CodeBlock title="player.anim.json" language="json" code={ANIM} />
      <ul>
        <li>
          <code>spritesheet_path</code>, <code>tile_size</code>,{" "}
          <code>grid_offset</code>: how to cut the sheet.
        </li>
        <li>
          <code>animations</code>: named clips; each frame is a{" "}
          <code>variant_id</code> + <code>duration_ms</code>; <code>loop</code>{" "}
          and <code>fps</code> metadata.
        </li>
        <li>
          Runtime: <code>SpriteAnimationSet.load(...)</code> +{" "}
          <code>AnimationPlayer.update(dt_ms)</code>; pass{" "}
          <code>render_scale=</code> to <code>load()</code> to scale the sheet
          and its atlas grid together.
        </li>
      </ul>

      <h2 id="particles">PARTICLE CONFIGS</h2>
      <p>
        Emitters placed in the editor land as nodes. The parser exposes them via{" "}
        <code>parse_nodes_file</code> (<code>ParsedNode</code>);{" "}
        <code>parse_particle_dict</code>/<code>parse_particle_file</code> parse
        config dicts. The same fields construct{" "}
        <code>ParticleSystemConfig</code> in code.
      </p>
      <CodeBlock title="map.nodes.json: a particle emitter node" language="json" code={NODE} />

      <Callout kind="tip" title="WHY THE EDITOR">
        Every format above round-trips through tilemap-editor. Using the editor
        for maps + collision means the JSON never drifts from what the parser
        expects.
      </Callout>
    </div>
  );
}
