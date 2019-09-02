import pygame
from cmg import color
from cmg.input import InputManager
from cmg.input import MouseButtons
from cmg.input import Keys
from cmg.input import KeyMods
from cmg.math import Vec2


class Application:
    instance = None

    def __init__(self, title="New CMG Application", width=800, height=600):
        Application.instance = self
        pygame.init()

        # Create the window
        self.screen = pygame.display.set_mode([width, height])
        pygame.display.set_caption(title)

        # Initialize clipboard
        pygame.scrap.init()

        self.clock = pygame.time.Clock()
        self.running = False
        self.framerate = 60
        self.inputs = []
        self.input = InputManager()

    def quit(self):
        self.running = False

    def update(self, dt):
        pass

    def draw(self):
        pass

    def run(self):
        self.running = True
        while self.running:
            # Event processing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    self.input.on_key_down(Keys(event.key), KeyMods(event.mod), event.unicode)
                elif event.type == pygame.KEYUP:
                    self.input.on_key_up(Keys(event.key), KeyMods(event.mod))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.input.on_mouse_down(Vec2(event.pos), MouseButtons(event.button))
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.input.on_mouse_up(Vec2(event.pos), MouseButtons(event.button))

            # Update
            self.input.update()
            self.update(dt=1.0 / self.framerate)

            # Draw
            self.screen.fill(tuple(color.WHITE))
            self.draw()
            pygame.display.flip()

            # Limit to 20 frames per second
            self.clock.tick(self.framerate)

        pygame.quit()
