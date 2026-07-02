"""
Rendering: viewport cull (cell-by-cell) vs chunked cull (32×32).

A sparse 500×500 procedurally generated tile grid (~15% filled).
Left panel scans the visible tile range cell-by-cell — every cell in
the viewport is visited and checked against the tile map.
Right panel uses a pre-built 32×32 chunk index — empty chunks are
skipped entirely, only populated chunks are iterated.

Same sparse data, same camera (arrows to pan).  For typical sparse
grids the chunked version visits ~50× fewer "cells".
"""

import random
import sys
import time

import pygame

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1200, 700
TS = 16
GRID_W, GRID_H = 500, 500
FILL_RATIO = 0.15
CHUNK_SIZE = 32
CAM_SPEED = 500

_PALETTE = [
    (60, 120, 60), (80, 140, 80), (100, 160, 100), (50, 100, 50),
    (120, 80, 50), (140, 100, 60), (80, 80, 120), (100, 100, 140),
    (70, 70, 70), (110, 110, 90), (90, 130, 150), (150, 130, 80),
]

COLOR_BG = (15, 15, 22)
COLOR_DIVIDER = (60, 60, 80)
COLOR_CULL = (140, 200, 255)
COLOR_CHUNK = (140, 255, 140)
COLOR_CHUNK_LINE = (50, 50, 65)
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


def build_chunks(tile_map):
    chunks: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for tx, ty in tile_map:
        cx, cy = tx // CHUNK_SIZE, ty // CHUNK_SIZE
        chunks.setdefault((cx, cy), []).append((tx, ty))
    return chunks


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
    pygame.display.set_caption("Rendering: Viewport Cull vs Chunked")
    font = pygame.font.SysFont("monospace", 13)
    clock = pygame.time.Clock()

    tile_map = generate_tiles()
    chunks = build_chunks(tile_map)
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

        # ── Left: Viewport Cull (cell-by-cell) ──
        screen.set_clip(left_rect)
        t0 = time.perf_counter_ns()
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
                sx = tx * TS - cam_x
                sy = ty * TS - cam_y
                pygame.draw.rect(screen, color, (sx, sy, TS, TS))
                cull_drawn += 1
        t1 = time.perf_counter_ns()

        # ── Divider ──
        pygame.draw.line(screen, COLOR_DIVIDER, (mid, 0), (mid, SCREEN_H), 3)

        # ── Right: Chunked ──
        screen.set_clip(right_rect)
        t2 = time.perf_counter_ns()
        chunk_visited = 0
        chunk_drawn = 0
        min_cx = max(0, int(cam_x // TS // CHUNK_SIZE))
        max_cx = min(GRID_W // CHUNK_SIZE, int((cam_x + panel_w) // TS // CHUNK_SIZE) + 1)
        min_cy = max(0, int(cam_y // TS // CHUNK_SIZE))
        max_cy = min(GRID_H // CHUNK_SIZE, int((cam_y + SCREEN_H) // TS // CHUNK_SIZE) + 1)
        for cx in range(min_cx, max_cx):
            for cy in range(min_cy, max_cy):
                chunk_visited += 1
                chunk_tiles = chunks.get((cx, cy))
                if chunk_tiles is None:
                    continue
                for tx, ty in chunk_tiles:
                    sx = tx * TS - cam_x + right_rect.x
                    sy = ty * TS - cam_y
                    pygame.draw.rect(screen, tile_map[(tx, ty)], (sx, sy, TS, TS))
                    chunk_drawn += 1
        t3 = time.perf_counter_ns()

        screen.set_clip(old_clip)

        # ── Info ──
        chunk_reduction = (1 - chunk_visited / max(cull_visited, 1)) * 100
        for px, label, color, v, d, ns, red in [
            (0, "Cull (cell-by-cell)", COLOR_CULL, cull_visited, cull_drawn, t1 - t0, None),
            (mid + 3, "Chunked (32\u00d732)", COLOR_CHUNK, chunk_visited, chunk_drawn, t3 - t2, chunk_reduction),
        ]:
            draw_panel_info(screen, font, px, label, color, total_tiles, v, d, ns, red)

        # ── Chunk grid overlay on right panel ──
        screen.set_clip(right_rect)
        for cx in range(min_cx, max_cx + 1):
            lx = cx * CHUNK_SIZE * TS - cam_x + right_rect.x
            if right_rect.x <= lx <= right_rect.right:
                pygame.draw.line(screen, COLOR_CHUNK_LINE, (lx, right_rect.top), (lx, right_rect.bottom), 1)
        for cy in range(min_cy, max_cy + 1):
            ly = cy * CHUNK_SIZE * TS - cam_y
            if 0 <= ly <= SCREEN_H:
                pygame.draw.line(screen, COLOR_CHUNK_LINE, (right_rect.left, ly), (right_rect.right, ly), 1)
        screen.set_clip(old_clip)

        # Legend
        lw, lh = 660, 22
        lpanel = pygame.Surface((lw, lh), pygame.SRCALPHA)
        lpanel.fill((0, 0, 0, 150))
        screen.blit(lpanel, (8, SCREEN_H - 26))
        legend = font.render(
            f"{GRID_W}x{GRID_H} grid  ({total_tiles:,} tiles, {FILL_RATIO:.0%} fill)  "
            f"Chunk {CHUNK_SIZE}x{CHUNK_SIZE}  Arrows pan  ESC exit",
            True, (200, 200, 210),
        )
        screen.blit(legend, (14, SCREEN_H - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
