import pygame

from src.core.scene import LevelScene
from src.settings import FPS, HEIGHT, WIDTH


class Game:
    __slots__ = ("screen", "clock", "running", "scene", "current_level")

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Platformer")

        self.clock = pygame.time.Clock()
        self.running = True
        self.current_level = 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.scene.player:
                        self.scene.player.shoot_bullet()

                elif event.key == pygame.K_1:
                    self.scene.emit_bullet_burst()

    def _on_scene_transition(self, old_scene):
        self.current_level += 1
        level_name = f"level{self.current_level}"
        self.scene = LevelScene(
            level_name=level_name,
            on_transition_complete=self._on_scene_transition,
        )

    def run(self):
        self.scene = LevelScene(on_transition_complete=self._on_scene_transition)

        while self.running:
            dt = self.clock.tick(FPS) / 1000

            self.handle_events()
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
