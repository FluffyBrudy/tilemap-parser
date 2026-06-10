"""
Particle system example — two loading approaches side by side.

Approach A — via TilemapData.load (recommended):
    Use this when you already load a map. Nodes are auto-discovered from the
    `nodes_dir` parameter (or the built-in heuristics if omitted). The parsed
    particle emitters live in `td.particle_emitters` as ParticleEmitterNode
    objects, each carrying a ready-to-use ParticleSystemConfig.

    Usage::

        td = TilemapData.load("path/to/map.json", nodes_dir="path/to/nodes")
        for emitter_node in td.particle_emitters:
            ps = ParticleSystem(emitter_node.config)
            ps.update(dt, x, y, w, h)
            ps.draw(screen, offset_x, offset_y, zoom)

Approach B — via parse_nodes_file + ParticleEmitterNode (explicit):
    Use this when you don't have a map or want full control over node loading.
    The steps are: parse the node JSON, filter for particle_emitter nodes, wrap
    each in ParticleEmitterNode, create a ParticleSystem, then update/draw.

    Usage::

        raw = parse_nodes_file("path/to/nodes/map.nodes.json")
        for node in raw:
            if node.node_type == "particle_emitter":
                pe = ParticleEmitterNode(node)
                ps = ParticleSystem(pe.config)
                ...

Rendering cycle (both approaches):
    Per frame, call `ps.update(dt, area_x, area_y, area_w, area_h)` then
    `ps.draw(screen, offset_x, offset_y, zoom)`. Zoom applies to both particle
    size and screen offset. Use offset to scroll the camera.

Modifying parameters at runtime (⚠️  not recommended):
    You *can* mutate ParticleSystemConfig fields directly on `ps.config` and
    then call `ps.set_config(ps.config)` to sync the emitter and renderer.
    This is fragile for anything beyond quick prototyping. If you need complex
    runtime editing (sliders, colour pickers, emission-shape switches), build a
    dedicated form editor instead — messing with config fields at runtime is a
    fast path to inconsistent state.
"""

import sys
from pathlib import Path

import pygame

from tilemap_parser.parser.node_parse import parse_nodes_file
from tilemap_parser.runtime.map_loader import TilemapData
from tilemap_parser.runtime.particles import ParticleEmitterNode, ParticleSystem

BASE = Path(__file__).resolve().parent.parent
NODES_DIR = BASE / "data" / "nodes"
MAP_PATH = BASE / "data" / "map.json"

SCREEN_W, SCREEN_H = 800, 600
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Particle System — two loading approaches")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    map_path = BASE / "data" / "map.json"
    # Approach 1: via TilemapData.load (map loader)
    td = TilemapData.load(map_path, nodes_dir=NODES_DIR)
    left_systems = []
    for pe_node in td.particle_emitters:
        ps = ParticleSystem(pe_node.config)
        ps.emit_burst(
            40, pe_node.rect.x, pe_node.rect.y, pe_node.rect.w, pe_node.rect.h
        )
        left_systems.append((ps, pe_node.rect, pe_node.name))

    # Approach 2: via parse_nodes_file (explicit)
    raw = parse_nodes_file(NODES_DIR / "map.nodes.json")
    raw_emitters = [n for n in raw if n.node_type == "particle_emitter"]
    right_systems = []
    for node in raw_emitters:
        pe_node = ParticleEmitterNode(node)
        ps = ParticleSystem(pe_node.config)
        ps.emit_burst(
            40, pe_node.rect.x, pe_node.rect.y, pe_node.rect.w, pe_node.rect.h
        )
        right_systems.append((ps, pe_node.rect, pe_node.name))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((20, 20, 30))

        #  left: map-loader approach
        label1 = font.render("TilemapData.load + nodes_dir", True, (200, 200, 100))
        screen.blit(label1, (30, 20))

        mx, my = pygame.mouse.get_pos()
        for ps, rect, name in left_systems:
            ps.update(dt, 160, 280, rect.w, rect.h)
            ps.draw(screen, 0, 0, 1)
            lx, ly = 160, 280
            pygame.draw.rect(screen, (100, 200, 100), (lx, ly, rect.w, rect.h), 1)
            nlabel = font.render(name, True, (100, 200, 100))
            screen.blit(nlabel, (lx, ly - 18))

        #  right: explicit approach
        label2 = font.render(
            "parse_nodes_file + ParticleEmitterNode", True, (100, 200, 200)
        )
        screen.blit(label2, (420, 20))

        for ps, rect, name in right_systems:
            ps.update(dt, 580, 280, rect.w, rect.h)
            ps.draw(screen, 0, 0, 1)
            rx, ry = 580, 280
            pygame.draw.rect(screen, (100, 200, 200), (rx, ry, rect.w, rect.h), 1)
            nlabel = font.render(name, True, (100, 200, 200))
            screen.blit(nlabel, (rx, ry - 18))

        #  click burst
        if pygame.mouse.get_pressed()[0]:
            mpos = (mx - 16, my - 16, 32, 32)
            for ps, _, _ in left_systems:
                ps.emit_burst(5, *mpos)
            for ps, _, _ in right_systems:
                ps.emit_burst(5, *mpos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
