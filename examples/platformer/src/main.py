import pygame

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
    
    def run(self):
        pass

if __name__ == "__main__":
    import os
    os.system("tilemap-editor run")
    
