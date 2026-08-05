import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function CameraGuide() {
  return (
    <div className="content">
      <h1>Camera: following the action</h1>
      <p>
        The <code>Camera</code> class handles viewport offsetting. It tracks a target
        with options for deadzones, smoothing (lerp), bounding boxes, and screen shake.
      </p>

      <h2 id="setup">SETUP AND MODES</h2>
      <p>
        Create a camera by passing the screen dimensions. You can choose between
        different tracking modes like <code>"centered"</code> or <code>"deadzone"</code>.
      </p>

      <CodeBlock
        title="camera_setup.py"
        code={`from tilemap_parser import Camera

# 800x600 viewport
camera = Camera(800, 600, mode="deadzone")

# Set the deadzone rectangle (x, y, w, h)
camera.set_deadzone(300, 200, 200, 200)

# Optional: clamp the camera so it never views outside the map boundaries
# camera.set_bounds(0, 0, map_width_px, map_height_px)`}
      />

      <h2 id="update">UPDATE AND DRAW</h2>
      <p>
        Tell the camera who to follow, update it every frame with <code>dt</code>,
        and then use its <code>offset</code> property when drawing.
      </p>

      <CodeBlock
        title="camera_update.py"
        code={`# 1. Target must have x, y attributes
camera.follow(player)

# 2. Update camera physics (smoothing, shake)
camera.update(dt)

# 3. Use camera.offset to draw
# TileLayerRenderer accepts the offset directly:
renderer.render(screen, camera.offset)

# For sprites, subtract the offset:
draw_x = player.x - camera.offset.x
draw_y = player.y - camera.offset.y
screen.blit(player_img, (draw_x, draw_y))`}
      />

      <h2 id="shake">SCREEN SHAKE</h2>
      <p>
        The camera includes a built-in screen shake effect, useful for impacts and explosions.
      </p>

      <CodeBlock
        title="shake.py"
        code={`# Start a shake with intensity (pixels) and duration (seconds)
camera.shake(intensity=10.0, duration=0.5)`}
      />

      <Callout kind="tip" title="SMOOTHING">
        Set <code>camera.lerp_speed = 5.0</code> (or similar) to make the camera lag slightly behind the player for a smoother feel. A value of 0.0 disables smoothing.
      </Callout>
    </div>
  );
}
