import { motion } from "framer-motion";
import { apiConfig } from "../config/api-config";
import { ClassReference, FunctionReference } from "../components/ApiReference";

const classGroups = {
  "Map Data": apiConfig.classes.filter(c => 
    ["TilemapData", "ParsedMap", "ParsedLayer", "ParsedTile", "ParsedTileset", "ParsedMeta", "ParsedObject", "ParsedObjectArea"].includes(c.name)
  ),
  "Animation": apiConfig.classes.filter(c => 
    ["SpriteAnimationSet", "AnimationPlayer", "AnimationClip", "AnimationLibrary", "AnimationFrame", "AnimationMarker"].includes(c.name)
  ),
  "Renderer": apiConfig.classes.filter(c => 
    ["TileLayerRenderer", "LayerRenderStats"].includes(c.name)
  ),
  "Errors": apiConfig.classes.filter(c => 
    ["MapParseError", "AnimationParseError"].includes(c.name)
  ),
};

export function ApiReference() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl"
    >
      <h2 className="text-2xl font-semibold text-zinc-100 mb-4">API Reference</h2>
      <p className="text-zinc-400 mb-8">
        Complete reference for {apiConfig.packageName} v{apiConfig.version}.
      </p>

      <section className="mb-12">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">Functions</h3>
        {apiConfig.functions.map((fn) => (
          <FunctionReference key={fn.name} fn={fn} />
        ))}
      </section>

      {Object.entries(classGroups).map(([groupName, classes]) => (
        classes.length > 0 && (
          <section key={groupName} className="mb-12">
            <h3 className="text-lg font-medium text-zinc-200 mb-4">{groupName}</h3>
            {classes.map((cls) => (
              <ClassReference key={cls.name} cls={cls} />
            ))}
          </section>
        )
      ))}
    </motion.div>
  );
}