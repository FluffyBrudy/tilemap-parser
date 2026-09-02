import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function MapParsing() {
  return (
    <div className="content">
      <h1>Map Parsing & Rendering</h1>
      <p>
        Loading a map is one call; rendering is one call per frame.{" "}
        <code>load_map()</code> parses the tilemap-editor JSON into a{" "}
        <code>TilemapData</code>, and <code>TileLayerRenderer</code> draws it
        with chunked culling.
      </p>

      <h2 id="loading-maps">LOADING MAPS</h2>
      <CodeBlock
        title="load_map.py"
        code={`from tilemap_parser import load_map

game_data = load_map("data/map.json")

print(f"Map size: {game_data.map_size}")     # (cols, rows)
print(f"Tile size: {game_data.tile_size}")   # (w, h), effective px
print(f"Render scale: {game_data.render_scale}")

# Layers, in draw order, filtered by type if you want:
for layer in game_data.get_layers(layer_type="tile"):
    print(layer.name, layer.z_index)`}
      />
      <p>
        The raw parsed structure lives on <code>game_data.parsed</code> (see the
        API reference's parsed data classes). For collision you usually want the
        layer as a flat grid: <code>game_data.build_tile_map()</code> collapses
        the tile layers into{" "}
        <code>
          {"{"}(col, row): tile_id{"}"}
        </code>
        , which is what <code>PhysicsWorld</code> owns.
      </p>

      <h2 id="rendering">TILE RENDERING</h2>
      <p>
        <code>TileLayerRenderer</code> draws only the visible chunks, respects
        layer <code>z_index</code> and <code>y_sort</code>, and reports what it
        did. The camera offset is passed per call; nothing is stored:
      </p>
      <CodeBlock
        title="game loop"
        code={`from tilemap_parser import TileLayerRenderer

renderer = TileLayerRenderer(game_data)

# In your game loop:
stats = renderer.render(screen, camera.offset)
# stats: LayerRenderStats: drawn_tiles, skipped_tiles, visible_layers`}
      />
      <ul>
        <li>
          <code>
            render(target, camera_xy, viewport_size=None, *, extra_objects=None,
            current_time_ms=None)
          </code>
          : <code>current_time_ms</code> drives tileset animations.
        </li>
        <li>
          <code>extra_objects</code> lets you blit sprites in the same pass (any
          objects with <code>surface</code>, <code>x</code>, <code>y</code>),
          after the tile layers.
        </li>
        <li>
          <code>warm_cache()</code> pre-bakes every tile variant up front, then
          frees the source data.
        </li>
      </ul>
      <Callout kind="tip" title="TILE CACHING">
        The renderer caches baked tile variants internally. If you swap tileset
        textures at runtime, call <code>clear_texture_caches()</code> to drop
        the cached surfaces, then let the renderer re-bake on demand.
      </Callout>

      <h2 id="overlays">RENDERING &amp; COLLISION OVERLAYS</h2>
      <p>
        The renderer is <strong>collision-blind</strong>: it draws tile{" "}
        <em>textures</em> from each layer's <code>ttype</code> /{" "}
        <code>variant</code> and has no idea whether a tile is solid, one-way,
        or air. Collision facts live in the world — <code>world.tile_map</code>{" "}
        plus the collision tileset. The split is deliberate: render everything,
        collide with a subset (<code>exclude_layers</code> only affects the
        world).
      </p>
      <p>
        Want debug overlays — say, dashed edges on one-way platforms? Ask the{" "}
        <em>world</em>, not the renderer:
      </p>
      <CodeBlock
        title="overlay.py"
        code={`tile_id = world.tile_map.get((tx, ty))          # world id space
if tile_id is None:
    continue
tile_data = world.tileset_collision.tiles.get(tile_id)
if tile_data is None:
    continue
if any(s.one_way for s in tile_data.shapes):
    # dashed top edge at (tx * world.tile_size[0], ty * world.tile_size[1])`}
      />
      <p>
        <code>one_way</code> is authored per polygon in the collision JSON —{" "}
        <em>never</em> in the map JSON — and the platformer family honors it
        automatically (blocks from above, passes from below), so the query is
        for <em>visuals</em> only. Two id-space caveats:
      </p>
      <ul>
        <li>
          The renderer keys tiles by layer <code>ttype</code>; the world keys by
          the collision tile id. Same map, same ints — until{" "}
          <code>use_gids=True</code> makes the world's ids global and the two
          spaces diverge. Always query through <code>world.tile_map</code>,
          never through the renderer.
        </li>
        <li>
          Tiles with no collision entry draw fine but collide as air; layers in{" "}
          <code>exclude_layers</code> draw fine but don't exist for physics.
        </li>
      </ul>

      <h2 id="objects">EXTRACTING OBJECTS</h2>
      <p>
        Object layers become <code>MapObject</code>s: pre-scaled surfaces,
        positions and collision shapes, ready to feed an{" "}
        <code>ObjectCollisionManager</code>. <code>load_map_objects</code> takes
        the map <em>and a directory</em> containing the matching{" "}
        <code>.object_collision.json</code> files:
      </p>
      <CodeBlock
        title="objects.py"
        code={`from tilemap_parser import load_map_objects, ObjectCollisionManager

objects = load_map_objects(game_data, "data/object_collision")

manager = ObjectCollisionManager()
for obj in objects:
    manager.add_object(obj)

player_start = next((o for o in objects if o.name == "PlayerStart"), None)
if player_start is not None:
    player.x, player.y = player_start.x, player_start.y`}
      />
      <ul>
        <li>
          Every object layer is iterated; there is no per-layer filter. The
          first region's layer/mask are adopted by the object.
        </li>
        <li>
          <code>require_collision=True</code> (the default) returns only objects
          that have matching collision regions; pass <code>False</code> to also
          get visual-only objects (with empty shapes).
        </li>
        <li>
          All spatial data is pre-scaled by the map's <code>render_scale</code>;
          no scaling on your side.
        </li>
      </ul>

      <h2 id="background">BACKGROUND (IMAGE) LAYERS</h2>
      <p>
        Image layers hold a single external image — a parallax sky, backdrop, or
        full-screen art. They carry no tiles or objects, just{" "}
        <code>image_path</code> and <code>image_rect</code>. The parser parses
        all image-layer metadata as <code>ParsedLayer</code> with{" "}
        <code>layer_type == "image"</code> (aliases{" "}
        <code>"background"</code> / <code>"background_layer"</code> are also
        accepted) but <code>TilemapData.load</code> eagerly loads only the first
        image layer into <code>TilemapData.background_layer</code>; additional
        image layers remain in <code>data.parsed.layers</code> for manual loading.
      </p>
      <CodeBlock
        title="background.py"
        code={`data = load_map("data/map.json")

bg = data.background_layer      # BackgroundLayer | None
if bg is not None and bg.surface is not None:
    # bg.image_path, bg.image_rect (x,y,w,h), bg.surface
    pos = (bg.image_rect[0], bg.image_rect[1]) if bg.image_rect else (0, 0)
    screen.blit(bg.surface, pos)

# Or query any image layer directly:
for layer in data.get_layers(layer_type="image"):
    print(layer.name, layer.image_path, layer.image_rect)`}
      />
      <ul>
        <li>
          <code>image_path</code>: project-relative path; resolved against the
          map directory (and <code>extra_search_base</code> if given). Missing
          files produce a warning and <code>surface == None</code> only when{" "}
          <code>skip_missing_images</code> is enabled (default{" "}
          <code>true</code>); when <code>skip_missing_images=False</code>,
          loading raises <code>MapParseError</code>.
        </li>
        <li>
          <code>image_rect</code>: pixel rect <code>(x, y, w, h)</code> where
          the image is drawn. <code>None</code> when not authored.
        </li>
        <li>
          Only the first image/background layer is exposed as{" "}
          <code>background_layer</code>; all are still in{" "}
          <code>data.parsed.layers</code>.
        </li>
      </ul>
    </div>
  );
}
