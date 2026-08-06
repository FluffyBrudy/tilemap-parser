"""Persistent field: a mist layer that already exists and only moves.

The three ways to use particles:
  - burst:   emit_burst(N, ...)   — explosions, one-off events
  - emitter: spawn_rate > 0        — rain, embers, smoke (born and die)
  - field:   emit_field(...)      — fog, haze, dust: fill once, wrap, never die

A field is config.wrap=True + config.spawn_rate=0, filled once with
emit_field().  Nothing is ever born or dies, so there are no alpha pops
and no churn cost.  Density is a dimensionless coverage — press
LEFT/RIGHT to feel how the count follows it.
"""

import sys

import pygame

from tilemap_parser import FOG_PROFILE, ParticleField

SCREEN_W, SCREEN_H = 800, 600
FPS = 60
BG = (24, 26, 32)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Persistent field — fog with wrap")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    # Padded a bit so sheets leave the screen before they wrap.
    rect = (-80, -80, SCREEN_W + 160, SCREEN_H + 160)
    density = 1.0
    mist = ParticleField(
        area=rect,
        profile=FOG_PROFILE,
        color=(200, 205, 215),
        density=density,
        global_alpha=1.0,
        direction=90,
        speed=(8, 8),
        quality="medium",
    )
    dust = ParticleField(
        area=rect,
        shape="smoke",
        color=(180, 150, 100),
        alpha=7,
        density=0.35,
        direction=180,
        speed=(3, 8),
        size=(20, 45),
        spread=45,
        quality="low",
    )

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    density += -0.1 if event.key == pygame.K_LEFT else 0.1
                    density = max(0.1, min(2.0, density))
                    mist.set_density(density)

        mist.update(dt)
        dust.update(dt)

        screen.fill(BG)
        mist.draw(screen)
        dust.draw(screen)

        n = sum(len(layer.system.emitter.particles) for layer in mist.layers + dust.layers)
        label = font.render(
            f"density {density:.1f}  ({n} sheets)   LEFT/RIGHT to change",
            True,
            (180, 190, 210),
        )
        screen.blit(label, (16, 16))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
