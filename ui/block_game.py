import pygame
import sys

pygame.init()

WIDTH = 800
HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)


class BlockGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simple Block Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.player = pygame.Rect(50, HEIGHT - 60, 40, 40)

        self.obstacles = [
            pygame.Rect(200, 400, 60, 60),
            pygame.Rect(350, 300, 80, 40),
            pygame.Rect(500, 450, 50, 50),
            pygame.Rect(650, 350, 70, 70),
            pygame.Rect(150, 200, 40, 80),
            pygame.Rect(400, 150, 90, 30),
        ]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        pass

    def draw(self):
        self.screen.fill(WHITE)

        pygame.draw.rect(self.screen, BLUE, self.player)

        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, RED, obstacle)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = BlockGame()
    game.run()
