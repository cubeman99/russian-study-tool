from cmg.input import *
from cmg.graphics import *

class Application:

  def __init__(self, title="New CMG Application", width=800, height=600):
    pygame.init()

    # Create the window
    self.screen = pygame.display.set_mode([width, height])
    pygame.display.set_caption(title)

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
      keys = pygame.key.get_pressed()
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.quit()
        elif event.type == pygame.KEYDOWN:
          self.input.on_key_down(event.key)
        elif event.type == pygame.KEYUP:
          self.input.on_key_up(event.key)

      # Update
      self.input.update()
      self.update(dt=1.0 / self.framerate)

      # Draw
      self.screen.fill(WHITE)
      self.draw()
      pygame.display.flip()

      # Limit to 20 frames per second
      self.clock.tick(self.framerate)
    
    pygame.quit()

