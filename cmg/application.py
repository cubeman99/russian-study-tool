import pygame
import queue
import time
import traceback
import cmg
from cmg.input import InputManager
from cmg.input import MouseButtons
from cmg.input import Keys
from cmg.input import KeyMods
from cmg.event import Event


class Application:
    instance = None

    def __init__(self, title="New CMG Application", width=800, height=600):
        Application.instance = self
        pygame.init()
        pygame.mixer.init()

        # Create the window
        self.screen = pygame.display.set_mode(
            [width, height], flags=pygame.RESIZABLE)
        #self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(title)

        # Initialize clipboard
        pygame.scrap.init()

        self.clock = pygame.time.Clock()
        self.running = False
        self.framerate = 60
        self.inputs = []
        self.input = InputManager()
        self.__fps = 0
        self.__frame_counter = 0

    def get_frame_rate(self) -> float:
        return self.__fps

    def quit(self):
        self.running = False
        self.on_quit()

    def on_quit(self):
        pass

    def on_window_resized(self, size: cmg.Vec2):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass

    def run(self):
        self.running = True
        self.__fps = 0.0
        self.__frame_counter = 0
        self.__frame_count_start_time = time.time()

        try:
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
                        self.input.on_mouse_down(cmg.Vec2(event.pos), MouseButtons(event.button))
                    elif event.type == pygame.MOUSEBUTTONUP:
                        self.input.on_mouse_up(cmg.Vec2(event.pos), MouseButtons(event.button))
                    elif event.type == pygame.VIDEORESIZE:
                        self.screen = pygame.display.set_mode(
                            (event.w, event.h), flags=pygame.RESIZABLE)
                        self.on_window_resized(cmg.Vec2(event.size))

                # Process queued events
                try:
                    while True:
                        event, args, handlers = Event.event_queue.get_nowait()
                        for handler in handlers:
                            handler(*args)
                except queue.Empty:
                    pass

                # Update
                self.input.update()
                self.update(dt=1.0 / self.framerate)

                # Draw
                self.screen.fill(tuple(cmg.Theme.color_background))
                self.draw()
                pygame.display.flip()
            
                # Update FPS counter
                now = time.time()
                self.__frame_counter += 1
                if now - self.__frame_count_start_time >= 1.0:
                    self.__fps = self.__frame_counter
                    self.__frame_counter = 1
                    self.__frame_count_start_time -= 1.0
                    if now - self.__frame_count_start_time >= 1.0:
                        self.__frame_count_start_time = now

                # Limit to 20 frames per second
                self.clock.tick(self.framerate)
        except:
            traceback.print_exc()
            self.on_quit()
            
        pygame.mixer.quit()
        pygame.quit()
