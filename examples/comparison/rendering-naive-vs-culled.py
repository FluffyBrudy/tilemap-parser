"""
Rendering: naive (draw every tile) vs viewport cull.

A sparse 500×500 procedurally generated tile grid (~15% filled).
Left panel draws ALL tiles every frame unconditionally.
Right panel computes the visible tile range and only draws what's
on screen.  Same camera (arrows), same sparse data.

Draw time and cells visited shown per method.
"""

import random
import sys
import time

import pygame

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1200, 700
TS = 16  # tile size (px)
GRID_W, GRID_H = 500, 500  # 250 000 cells
FILL_RATIO = 0.15  # ~37 500 tiles
CAM_SPEED = 500

_PALETTE = [
    (60, 120, 60), (80, 140, 80), (100, 160, 100), (50, 100, 50),
    (120, 80, 50), (140, 100, 60), (80, 80, 120), (100, 100, 140),
    (70, 70, 70), (110, 110, 90), (90, 130, 150), (150, 130, 80),
]

COLOR_BG = (15, 15, 22)
COLOR_DIVIDER = (60, 60, 80)
COLOR_DIM = (130, 130, 150)

WORLD_W = GRID_W * TS
WORLD_H = GRID_H * TS


def generate_tiles():
    rng = random.Random(42)
    tile_map: dict[tuple[int, int], tuple[int, int, int]] = {}
    for _ in range(int(GRID_W * GRID_H * FILL_RATIO)):
        tx = rng.randint(0, GRID_W - 1)
        ty = rng.randint(0, GRID_H - 1)
        tile_map[(tx, ty)] = rng.choice(_PALETTE)
    for _ in range(12):
        rx = rng.randint(0, GRID_W - 20)
        ry = rng.randint(0, GRID_H - 20)
        w, h = rng.randint(8, 20), rng.randint(8, 14)
        for dx in range(w):
            for dy in range(h):
                tx, ty = rx + dx, ry + dy
                if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                    tile_map[(tx, ty)] = rng.choice(_PALETTE)
    return tile_map


def draw_panel_info(screen, font, px, label, color, total, visited, drawn, ns, reduction=None):
    lines = [
        label,
        f"Total tiles:     {total:,}",
        f"Cells visited:   {visited:,}",
        f"Drawn this frame: {drawn:,}",
    ]
    if reduction is not None:
        lines.append(f"Reduction:       {reduction:.1f}%")
    lines.append(f"Draw time:       {ns / 1_000_000:.2f} ms")
    pw, ph = 220, len(lines) * 20 + 12
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 170))
    screen.blit(panel, (px + 4, 8))
    y = 14
    for text in lines:
        c = color if "time" in text else (230, 230, 230)
        screen.blit(font.render(text, True, c), (px + 10, y))
        y += 20


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Rendering: Naive vs Viewport Cull")
    font = pygame.font.SysFont("monospace", 13)
    clock = pygame.time.Clock()

    tile_map = generate_tiles()
    total_tiles = len(tile_map)
    mid = SCREEN_W // 2
    left_rect = pygame.Rect(0, 0, mid - 2, SCREEN_H)
    right_rect = pygame.Rect(mid + 3, 0, SCREEN_W - mid - 3, SCREEN_H)
    panel_w = right_rect.width

    cam_x, cam_y = 0.0, 0.0
    running = True
    while running:
        dt = clock.tick() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        cam_x += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * CAM_SPEED * dt
        cam_y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * CAM_SPEED * dt
        cam_x = max(0.0, min(WORLD_W - panel_w, cam_x))
        cam_y = max(0.0, min(WORLD_H - SCREEN_H, cam_y))

        screen.fill(COLOR_BG)
        old_clip = screen.get_clip()

        # ── Left: Naive (draw every tile unconditionally) ──
        screen.set_clip(left_rect)
        t0 = time.perf_counter_ns()
        naive_visited = total_tiles
        for (tx, ty), color in tile_map.items():
            sx = tx * TS - cam_x
            sy = ty * TS - cam_y
            pygame.draw.rect(screen, color, (sx, sy, TS, TS))
        t1 = time.perf_counter_ns()

        # ── Divider ──
        pygame.draw.line(screen, COLOR_DIVIDER, (mid, 0), (mid, SCREEN_H), 3)

        # ── Right: Viewport Cull ──
        screen.set_clip(right_rect)
        t2 = time.perf_counter_ns()
        cull_visited = 0
        cull_drawn = 0
        min_tx = max(0, int(cam_x // TS))
        max_tx = min(GRID_W, int((cam_x + panel_w) // TS) + 1)
        min_ty = max(0, int(cam_y // TS))
        max_ty = min(GRID_H, int((cam_y + SCREEN_H) // TS) + 1)
        for tx in range(min_tx, max_tx):
            for ty in range(min_ty, max_ty):
                cull_visited += 1
                color = tile_map.get((tx, ty))
                if color is None:
                    continue
                sx = tx * TS - cam_x + right_rect.x
                sy = ty * TS - cam_y
                pygame.draw.rect(screen, color, (sx, sy, TS, TS))
                cull_drawn += 1
        t3 = time.perf_counter_ns()

        screen.set_clip(old_clip)

        # ── Info ──
        cull_reduction = (1 - cull_visited / max(total_tiles, 1)) * 100
        for px, label, color, v, d, ns, red in [
            (0, "Naive (draw all)", (255, 140, 140), naive_visited, naive_visited, t1 - t0, None),
            (mid + 3, "Cull (viewport)", (140, 200, 255), cull_visited, cull_drawn, t3 - t2, cull_reduction),
        ]:
            draw_panel_info(screen, font, px, label, color, total_tiles, v, d, ns, red)

        # Legend
        lw, lh = 620, 22
        lpanel = pygame.Surface((lw, lh), pygame.SRCALPHA)
        lpanel.fill((0, 0, 0, 150))
        screen.blit(lpanel, (8, SCREEN_H - 26))
        legend = font.render(
            f"{GRID_W}x{GRID_H} grid  ({total_tiles:,} tiles, {FILL_RATIO:.0%} fill)  "
            f"Arrows pan  ESC exit",
            True, (200, 200, 210),
        )
        screen.blit(legend, (14, SCREEN_H - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
