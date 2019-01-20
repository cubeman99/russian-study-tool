
import pygame
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_cards.study_state import *
from study_cards.menu_state import *

# Define some colors
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
DEAD_ZONE = 0.01

class StudyCardsApp(Application):

  def __init__(self):
    self.title = "Russian Study Tool"
    Application.__init__(self, title=self.title, width=800, height=600)
    
    pygame.joystick.init()
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()

    self.clock = pygame.time.Clock()
    self.joystick_ready = False
    self.inputs = [
      Input(index=2, name="Middle", reversed=True, max=1, min=-1),
      Input(index=1, name="Left", reversed=True, max=1, min=-1),
      Input(index=3, name="Right", reversed=True, max=1, min=-1)]
   
    self.root = "data"
    self.states = [MenuState("")]
    self.state.app = self
    self.state.begin()
    self.graphics = Graphics(self.screen)
    
    self.input.bind(pygame.K_ESCAPE, pressed=self.quit)

  def pop_state(self):
    if len(self.states) == 1:
      self.quit()
    else:
      del self.states[-1]

  def push_state(self, state):
    state.app = self
    self.states.append(state)
    state.begin()

  def draw_text_box(self, text, x, y, width, height,
                    border_color=BLACK, border_width=2,
                    background_color=WHITE, text_color=BLACK):
    r = pygame.Rect(x, y, 0, 0)
    r.inflate_ip(width, height)
    self.graphics.fill_rect(r.x, r.y, r.width, r.height, color=background_color)
    self.graphics.draw_rect(r.x, r.y, r.width, r.height, thickness=2, color=border_color)
    self.graphics.draw_text(x, y, text, align=Align.Centered, color=text_color)
    
  @property
  def state(self):
    return self.states[-1]

  def update(self, dt):
    if not self.joystick_ready:
      for axis in range(self.joystick.get_numaxes()):
        if self.joystick.get_axis(axis) != 0:
          self.joystick_ready = True
    if self.joystick_ready:
      for index, input in enumerate(self.inputs):
        input.update(self.joystick.get_axis(input.index))
        self.state.buttons[index].update(
          dt=dt,
          is_down=input.amount > DEAD_ZONE,
          is_pressed=input.amount > DEAD_ZONE and input.prev_amount <= DEAD_ZONE)

    self.state.process_input()
    self.state.update(dt)

  def draw(self):
    self.screen.fill(WHITE)
    self.state.draw(self.graphics)
        
