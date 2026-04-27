import { useState } from "react";
import { motion } from "framer-motion";

export function JsonFormatsPage() {
  const [activeFormat, setActiveFormat] = useState<"tilemap" | "animation" | "tileset" | "character">("tilemap");

  const formats = [
    { id: "tilemap" as const, label: "Tilemap JSON", desc: ".json files from editor" },
    { id: "animation" as const, label: "Animation JSON", desc: ".anim.json sprite animations" },
    { id: "tileset" as const, label: "Tileset Collision", desc: ".collision.json tile polygons" },
    { id: "character" as const, label: "Character Collision", desc: ".collision.json character shapes" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-4xl space-y-8"
    >
      <div>
        <h2 className="text-2xl font-semibold text-zinc-100 mb-2">JSON Format Reference</h2>
        <p className="text-zinc-400">
          Complete specification of all JSON formats produced by tilemap-editor and parsed by tilemap-parser.
        </p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {formats.map(fmt => (
          <button
            key={fmt.id}
            onClick={() => setActiveFormat(fmt.id)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              activeFormat === fmt.id
                ? "bg-zinc-700 text-zinc-100"
                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300"
            }`}
          >
            {fmt.label}
          </button>
        ))}
      </div>

      {activeFormat === "tilemap" && <TilemapFormat />}
      {activeFormat === "animation" && <AnimationFormat />}
      {activeFormat === "tileset" && <TilesetCollisionFormat />}
      {activeFormat === "character" && <CharacterCollisionFormat />}
    </motion.div>
  );
}

function TilemapFormat() {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    meta: true,
    resources: true,
    data: true,
    project_state: false,
  });

  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-lg font-medium text-zinc-200 mb-2">Tilemap JSON</h3>
        <p className="text-sm text-zinc-500">Format: .json | Root keys: meta, resources, project_state, data</p>
      </div>

      <Section title="meta" expanded={expanded.meta} onToggle={() => setExpanded(e => ({ ...e, meta: !e.meta }))}>
        <p className="text-sm text-zinc-400 mb-3">Map metadata and dimensions. Required.</p>
        <FieldTable fields={[
          { name: "tile_size", type: "string | [int, int]", required: true, description: 'Tile dimensions e.g. "32;32" or [32, 32]' },
          { name: "map_size", type: "string | [int, int]", description: 'Map size in tiles e.g. "50;50"' },
          { name: "initial_map_size", type: "string | [int, int]", description: "Original map size when created" },
          { name: "zoom_level", type: "float", default: "1.0", description: "Editor zoom level" },
          { name: "scroll", type: "string | [int, int]", default: '"0;0"', description: "Editor scroll position" },
          { name: "version", type: "string", default: '"1.1"', description: "Format version" },
        ]} />
        <CodeBlock code={`"meta": {
  "tile_size": "32;32",
  "map_size": "50;50",
  "zoom_level": 1.0,
  "scroll": "0;0",
  "version": "1.1"
}`} />
      </Section>

      <Section title="resources" expanded={expanded.resources} onToggle={() => setExpanded(e => ({ ...e, resources: !e.resources }))}>
        <p className="text-sm text-zinc-400 mb-3">Tileset definitions. Required. Supports two formats.</p>
        <h4 className="text-sm font-medium text-zinc-300 mb-2">Simple List Format</h4>
        <CodeBlock code={`"resources": ["tileset.png", "more_tiles.png"]`} />
        <h4 className="text-sm font-medium text-zinc-300 mb-2 mt-4">Detailed Object Format</h4>
        <CodeBlock code={`"resources": {
  "tilesets": [
    {
      "path": "terrain.png",
      "type": "tile",
      "properties": { "category": "ground" },
      "tile_properties": {
        "0": { "walkable": true },
        "5": { "climbable": true }
      }
    }
  ]
}`} />
      </Section>

      <Section title="data" expanded={expanded.data} onToggle={() => setExpanded(e => ({ ...e, data: !e.data }))}>
        <p className="text-sm text-zinc-400 mb-3">Tile and object layer data. Required.</p>
        <h4 className="text-sm font-medium text-zinc-300 mb-2">Layer Structure</h4>
        <FieldTable fields={[
          { name: "name", type: "string", required: true, description: "Layer name" },
          { name: "type", type: "string", required: true, description: '"tile" or "object"' },
          { name: "visible", type: "bool", default: "true", description: "Is layer visible" },
          { name: "locked", type: "bool", default: "false", description: "Is layer locked" },
          { name: "opacity", type: "float", default: "1.0", description: "Layer opacity 0-1" },
          { name: "z_index", type: "int", default: "layer_id", description: "Z-order for rendering" },
          { name: "tiles", type: "object", description: "Tile entries (tile layers only)" },
          { name: "objects", type: "object", description: "Object entries (object layers only)" },
        ]} />
        <h4 className="text-sm font-medium text-zinc-300 mb-2 mt-4">Tile Entry</h4>
        <CodeBlock code={`"5;5": {
  "pos": "5;5",
  "ttype": 0,
  "variant": 18,
  "properties": {}
}`} />
        <h4 className="text-sm font-medium text-zinc-300 mb-2 mt-4">Object Entry</h4>
        <CodeBlock code={`"0": {
  "area": { "x": 100, "y": 200, "w": 32, "h": 32 },
  "ttype": 1,
  "tileset_type": "object",
  "variant": 0,
  "properties": { "type": "chest" }
}`} />
      </Section>

      <Section title="project_state" expanded={expanded.project_state} onToggle={() => setExpanded(e => ({ ...e, project_state: !e.project_state }))}>
        <p className="text-sm text-zinc-400 mb-3">Autotile rules and groups. Optional.</p>
        <CodeBlock code={`"project_state": {
  "rules": [
    {
      "name": "wall_rule",
      "neighbors": [[1, 0], [0, 1]],
      "tileset_path": "terrain.png",
      "tileset_index": 0,
      "variant_ids": [0, 1, 2, 3],
      "group_id": "walls"
    }
  ],
  "groups": [
    { "name": "walls", "rules": [...] }
  ]
}`} />
      </Section>
    </div>
  );
}

function AnimationFormat() {
  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-lg font-medium text-zinc-200 mb-2">Animation JSON</h3>
        <p className="text-sm text-zinc-500">Format: .anim.json | Root keys: spritesheet_path, tile_size, animations</p>
      </div>

      <Section title="Root" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Animation library root object.</p>
        <FieldTable fields={[
          { name: "spritesheet_path", type: "string", description: "Path to sprite sheet image" },
          { name: "tile_size", type: "[int, int]", default: "[32, 32]", description: "[width, height] of each frame" },
          { name: "animations", type: "object", required: true, description: "Dictionary of animation clips" },
        ]} />
        <CodeBlock code={`{
  "spritesheet_path": "hero_sheet.png",
  "tile_size": [32, 32],
  "animations": {
    "idle": { ... },
    "walk": { ... },
    "attack": { ... }
  }
}`} />
      </Section>

      <Section title="Animation Clip" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">A single animation sequence.</p>
        <FieldTable fields={[
          { name: "name", type: "string", description: "Animation name (or use object key)" },
          { name: "frames", type: "array", required: true, description: "List of animation frames" },
          { name: "loop", type: "bool", default: "true", description: "Whether animation loops" },
          { name: "fps", type: "float", default: "60.0", description: "Target frames per second" },
          { name: "metadata", type: "object", description: "Custom metadata" },
          { name: "markers", type: "array", description: "Named frame markers {name, frame_index}" },
        ]} />
        <CodeBlock code={`"idle": {
  "name": "idle",
  "frames": [
    { "variant_id": 0, "duration_ms": 100.0 },
    { "variant_id": 1, "duration_ms": 100.0 },
    { "variant_id": 2, "duration_ms": 100.0 }
  ],
  "loop": true,
  "fps": 60.0,
  "markers": [
    { "name": "attack_start", "frame_index": 5 }
  ]
}`} />
      </Section>

      <Section title="Frame" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Single frame in an animation clip.</p>
        <FieldTable fields={[
          { name: "variant_id", type: "int", required: true, description: "Sprite cell index in sheet" },
          { name: "duration_ms", type: "float", default: "100.0", description: "Frame duration in milliseconds" },
        ]} />
        <CodeBlock code={`{ "variant_id": 5, "duration_ms": 150.0 }`} />
      </Section>
    </div>
  );
}

function TilesetCollisionFormat() {
  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-lg font-medium text-zinc-200 mb-2">Tileset Collision JSON</h3>
        <p className="text-sm text-zinc-500">Format: .collision.json (sidecar) | Root keys: tileset_name, tile_size, tiles</p>
      </div>

      <Section title="Root" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Tileset collision root object.</p>
        <FieldTable fields={[
          { name: "tileset_name", type: "string", required: true, description: "Name of the tileset" },
          { name: "tile_size", type: "[int, int]", required: true, description: "[width, height] of tiles" },
          { name: "tiles", type: "object", required: true, description: "Per-tile collision data keyed by variant" },
        ]} />
        <CodeBlock code={`{
  "tileset_name": "terrain",
  "tile_size": [32, 32],
  "tiles": {
    "0": { ... },
    "5": { ... }
  }
}`} />
      </Section>

      <Section title="Tile Collision" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Collision data for a single tile variant.</p>
        <FieldTable fields={[
          { name: "tile_id", type: "int", required: true, description: "Tile variant ID" },
          { name: "shapes", type: "array", required: true, description: "List of collision shapes" },
        ]} />
        <CodeBlock code={`"0": {
  "tile_id": 0,
  "shapes": [
    {
      "type": "polygon",
      "vertices": [[1.0, 10.125], [14.375, 2.0], [30.0, 10.125], [30.0, 30.0], [1.0, 30.0]],
      "one_way": false
    }
  ]
}`} />
      </Section>

      <Section title="Collision Shape" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Polygon collision shape (currently only polygon type).</p>
        <FieldTable fields={[
          { name: "type", type: "string", default: '"polygon"', description: 'Shape type, currently only "polygon"' },
          { name: "vertices", type: "array of [x, y]", required: true, description: "List of vertex coordinates" },
          { name: "one_way", type: "bool", default: "false", description: "One-way platform (pass through from above)" },
        ]} />
        <CodeBlock code={`{
  "type": "polygon",
  "vertices": [[1.0, 10.125], [14.375, 2.0], [30.0, 10.125], [30.0, 30.0], [1.0, 30.0]],
  "one_way": false
}`} />
      </Section>
    </div>
  );
}

function CharacterCollisionFormat() {
  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-lg font-medium text-zinc-200 mb-2">Character Collision JSON</h3>
        <p className="text-sm text-zinc-500">Format: .collision.json (sidecar) | Root keys: name, shape, properties</p>
      </div>

      <Section title="Root" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Character collision root object.</p>
        <FieldTable fields={[
          { name: "name", type: "string", required: true, description: "Character name" },
          { name: "shape", type: "object", required: true, description: "Collision shape definition" },
          { name: "properties", type: "object", description: "Custom properties" },
        ]} />
      </Section>

      <Section title="Rectangle" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Standard rectangular hitbox.</p>
        <FieldTable fields={[
          { name: "type", type: "string", required: true, description: '"rectangle"' },
          { name: "width", type: "float", required: true, description: "Width of rectangle" },
          { name: "height", type: "float", required: true, description: "Height of rectangle" },
          { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
        ]} />
        <CodeBlock code={`{
  "type": "rectangle",
  "width": 32.0,
  "height": 48.0,
  "offset": [0.0, 0.0]
}`} />
      </Section>

      <Section title="Circle" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Circular hitbox.</p>
        <FieldTable fields={[
          { name: "type", type: "string", required: true, description: '"circle"' },
          { name: "radius", type: "float", required: true, description: "Circle radius" },
          { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
        ]} />
        <CodeBlock code={`{
  "type": "circle",
  "radius": 16.0,
  "offset": [0.0, 0.0]
}`} />
      </Section>

      <Section title="Capsule" expanded={true} onToggle={() => {}}>
        <p className="text-sm text-zinc-400 mb-3">Vertical capsule shape.</p>
        <FieldTable fields={[
          { name: "type", type: "string", required: true, description: '"capsule"' },
          { name: "radius", type: "float", required: true, description: "Capsule radius" },
          { name: "height", type: "float", required: true, description: "Total height including hemispheres" },
          { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
        ]} />
        <CodeBlock code={`{
  "type": "capsule",
  "radius": 8.0,
  "height": 32.0,
  "offset": [0.0, 0.0]
}`} />
      </Section>
    </div>
  );
}

function Section({ title, expanded, onToggle, children }: { title: string; expanded: boolean; onToggle: () => void; children: React.ReactNode }) {
  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-zinc-800/50 transition-colors"
      >
        <span className="font-mono text-zinc-200">{title}</span>
        <span className="text-zinc-500">{expanded ? "−" : "+"}</span>
      </button>
      {expanded && <div className="px-4 pb-4 space-y-3">{children}</div>}
    </div>
  );
}

function FieldTable({ fields }: { fields: { name: string; type: string; required?: boolean; default?: string; description: string }[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            <th className="text-left py-2 text-zinc-400 font-medium">Field</th>
            <th className="text-left py-2 text-zinc-400 font-medium">Type</th>
            <th className="text-left py-2 text-zinc-400 font-medium">Description</th>
          </tr>
        </thead>
        <tbody>
          {fields.map(field => (
            <tr key={field.name} className="border-b border-zinc-800/50">
              <td className="py-2 font-mono text-amber-400">{field.name}</td>
              <td className="py-2 font-mono text-zinc-500 text-xs">{field.type}{field.required && <span className="text-red-400">*</span>}</td>
              <td className="py-2 text-zinc-400 text-xs">{field.description}{field.default && <span className="text-zinc-600"> (default: {field.default})</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="bg-zinc-950 rounded-lg p-4 text-xs font-mono text-zinc-300 overflow-x-auto">
      {code}
    </pre>
  );
}