export interface JsonField {
  name: string;
  type: string;
  required?: boolean;
  default?: string;
  description: string;
}

export interface JsonStructure {
  name: string;
  description: string;
  fields: JsonField[];
  example: string;
  nested?: { key: string; description: string; fields?: JsonField[]; structure?: string }[];
}

export interface ShapeFormat {
  type: string;
  fields: JsonField[];
  example: string;
}

export const jsonFormats = {
  tilemap: {
    name: "Tilemap JSON",
    description: "Game level map format produced by tilemap-editor",
    fileExtension: ".json",
    rootKeys: ["meta", "resources", "project_state", "data"],
    sections: [
      {
        key: "meta",
        name: "Meta",
        description: "Map metadata and dimensions",
        required: true,
        fields: [
          { name: "tile_size", type: "string | [int, int]", required: true, description: 'Tile dimensions, e.g. "32;32" or [32, 32]' },
          { name: "map_size", type: "string | [int, int]", description: 'Map size in tiles, e.g. "50;50"' },
          { name: "initial_map_size", type: "string | [int, int]", description: "Original map size when created" },
          { name: "zoom_level", type: "float", default: "1.0", description: "Editor zoom level" },
          { name: "scroll", type: "string | [int, int]", default: '"0;0"', description: "Editor scroll position" },
          { name: "version", type: "string", default: '"1.1"', description: "Format version" },
        ],
        example: `"meta": {
  "tile_size": "32;32",
  "map_size": "50;50",
  "zoom_level": 1.0,
  "scroll": "0;0",
  "version": "1.1"
}`,
      },
      {
        key: "resources",
        name: "Resources",
        description: "Tileset definitions (simple list or detailed object format)",
        required: true,
        fields: [],
        simpleExample: `"resources": ["tileset.png", "more_tiles.png"]`,
        detailedExample: `"resources": {
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
}`,
      },
      {
        key: "data",
        name: "Data",
        description: "Tile and object layer data",
        required: true,
        fields: [],
        layersExample: `"data": {
  "layers": [
    {
      "name": "Terrain",
      "type": "tile",
      "visible": true,
      "locked": false,
      "opacity": 1.0,
      "z_index": 0,
      "tiles": {
        "5;5": { "pos": "5;5", "ttype": 0, "variant": 18 },
        "6;5": { "pos": "6;5", "ttype": 0, "variant": 19 }
      },
      "properties": {}
    },
    {
      "name": "Objects",
      "type": "object",
      "visible": true,
      "locked": false,
      "opacity": 1.0,
      "z_index": 1,
      "objects": {
        "0": {
          "area": { "x": 100, "y": 200, "w": 32, "h": 32 },
          "ttype": 1,
          "tileset_type": "object",
          "variant": 0,
          "properties": { "type": "chest" }
        }
      },
      "next_object_id": 1,
      "properties": {}
    }
  ]
}`,
        tileExample: `"5;5": { "pos": "5;5", "ttype": 0, "variant": 18, "properties": {} }`,
        tileFields: [
          { name: "pos", type: "string", required: true, description: 'Position "x;y"' },
          { name: "ttype", type: "int | string", required: true, description: "Tileset index or path" },
          { name: "variant", type: "int", required: true, description: "Tile variant ID in tileset" },
          { name: "properties", type: "object", description: "Custom tile properties" },
        ],
        objectExample: `"0": {
  "area": { "x": 100, "y": 200, "w": 32, "h": 32 },
  "ttype": 1,
  "tileset_type": "object",
  "variant": 0,
  "properties": {}
}`,
        objectFields: [
          { name: "area", type: "object", required: true, description: "Bounding box {x, y, w, h}" },
          { name: "ttype", type: "int", required: true, description: "Tileset index" },
          { name: "tileset_type", type: "string", default: '"object"', description: 'Tileset type, usually "object"' },
          { name: "variant", type: "int", required: true, description: "Tile variant" },
          { name: "properties", type: "object", description: "Custom object properties" },
        ],
      },
      {
        key: "project_state",
        name: "Project State",
        description: "Autotile rules and groups (optional)",
        fields: [],
        example: `"project_state": {
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
    {
      "name": "walls",
      "rules": [...]
    }
  ]
}`,
      },
    ],
  },

  animation: {
    name: "Animation JSON",
    description: "Sprite animation definitions",
    fileExtension: ".anim.json",
    rootKeys: ["spritesheet_path", "tile_size", "animations"],
    sections: [
      {
        key: "root",
        name: "Root",
        description: "Animation library root",
        fields: [
          { name: "spritesheet_path", type: "string", description: "Path to sprite sheet image" },
          { name: "tile_size", type: "[int, int]", default: "[32, 32]", description: "[width, height] of each frame" },
          { name: "animations", type: "object", required: true, description: "Dictionary of animation clips" },
        ],
        example: `{
  "spritesheet_path": "hero_sheet.png",
  "tile_size": [32, 32],
  "animations": {
    "idle": { ... },
    "walk": { ... },
    "attack": { ... }
  }
}`,
      },
      {
        key: "clip",
        name: "Animation Clip",
        description: "A single animation sequence",
        fields: [
          { name: "name", type: "string", description: "Animation name (or use object key)" },
          { name: "frames", type: "array", required: true, description: "List of animation frames" },
          { name: "loop", type: "bool", default: "true", description: "Whether animation loops" },
          { name: "fps", type: "float", default: "60.0", description: "Target frames per second" },
          { name: "metadata", type: "object", description: "Custom metadata" },
          { name: "markers", type: "array", description: "Named frame markers" },
        ],
        example: `"idle": {
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
}`,
      },
      {
        key: "frame",
        name: "Animation Frame",
        description: "Single frame in an animation clip",
        fields: [
          { name: "variant_id", type: "int", required: true, description: "Sprite cell index in sheet" },
          { name: "duration_ms", type: "float", default: "100.0", description: "Frame duration in milliseconds" },
        ],
        example: `{ "variant_id": 5, "duration_ms": 150.0 }`,
      },
    ],
  },

  tilesetCollision: {
    name: "Tileset Collision JSON",
    description: "Tile collision polygons (sidecar file)",
    fileExtension: ".collision.json",
    rootKeys: ["tileset_name", "tile_size", "tiles"],
    sections: [
      {
        key: "root",
        name: "Root",
        description: "Tileset collision root",
        fields: [
          { name: "tileset_name", type: "string", required: true, description: "Name of the tileset" },
          { name: "tile_size", type: "[int, int]", required: true, description: "[width, height] of tiles" },
          { name: "tiles", type: "object", required: true, description: "Per-tile collision data" },
        ],
        example: `{
  "tileset_name": "terrain",
  "tile_size": [32, 32],
  "tiles": {
    "0": { ... },
    "5": { ... }
  }
}`,
      },
      {
        key: "tile",
        name: "Tile Collision",
        description: "Collision data for a single tile",
        fields: [
          { name: "tile_id", type: "int", required: true, description: "Tile variant ID" },
          { name: "shapes", type: "array", required: true, description: "List of collision shapes" },
        ],
        example: `"0": {
  "tile_id": 0,
  "shapes": [
    {
      "type": "polygon",
      "vertices": [[1.0, 10.125], [14.375, 2.0], [30.0, 10.125], [30.0, 30.0], [1.0, 30.0]],
      "one_way": false
    }
  ]
}`,
      },
      {
        key: "shape",
        name: "Collision Shape",
        description: "Polygon collision shape",
        fields: [
          { name: "type", type: "string", default: '"polygon"', description: 'Shape type, currently only "polygon"' },
          { name: "vertices", type: "array of [x, y]", required: true, description: "List of vertex coordinates" },
          { name: "one_way", type: "bool", default: "false", description: "One-way platform (pass through from above)" },
        ],
        example: `{
  "type": "polygon",
  "vertices": [[1.0, 10.125], [14.375, 2.0], [30.0, 10.125], [30.0, 30.0], [1.0, 30.0]],
  "one_way": false
}`,
      },
    ],
  },

  characterCollision: {
    name: "Character Collision JSON",
    description: "Character/sprite collision shapes (sidecar file)",
    fileExtension: ".collision.json",
    rootKeys: ["name", "shape", "properties"],
    sections: [
      {
        key: "root",
        name: "Root",
        description: "Character collision root",
        fields: [
          { name: "name", type: "string", required: true, description: "Character name" },
          { name: "shape", type: "object", required: true, description: "Collision shape definition" },
          { name: "properties", type: "object", description: "Custom properties" },
        ],
        example: `{
  "name": "Player",
  "shape": { ... },
  "properties": { "speed": 150 }
}`,
      },
      {
        key: "shapes",
        name: "Shape Types",
        description: "Available collision shape types",
        fields: [],
        rectangle: {
          name: "Rectangle",
          description: "Standard rectangular hitbox",
          example: `{
  "type": "rectangle",
  "width": 32.0,
  "height": 48.0,
  "offset": [0.0, 0.0]
}`,
          fields: [
            { name: "type", type: "string", required: true, description: '"rectangle"' },
            { name: "width", type: "float", required: true, description: "Width of rectangle" },
            { name: "height", type: "float", required: true, description: "Height of rectangle" },
            { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
          ],
        },
        circle: {
          name: "Circle",
          description: "Circular hitbox",
          example: `{
  "type": "circle",
  "radius": 16.0,
  "offset": [0.0, 0.0]
}`,
          fields: [
            { name: "type", type: "string", required: true, description: '"circle"' },
            { name: "radius", type: "float", required: true, description: "Circle radius" },
            { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
          ],
        },
        capsule: {
          name: "Capsule",
          description: "Vertical capsule shape",
          example: `{
  "type": "capsule",
  "radius": 8.0,
  "height": 32.0,
  "offset": [0.0, 0.0]
}`,
          fields: [
            { name: "type", type: "string", required: true, description: '"capsule"' },
            { name: "radius", type: "float", required: true, description: "Capsule radius" },
            { name: "height", type: "float", required: true, description: "Total height including hemispheres" },
            { name: "offset", type: "[float, float]", default: "[0.0, 0.0]", description: "Offset from sprite origin" },
          ],
        },
      },
    ],
  },
};