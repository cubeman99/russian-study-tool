import pygame
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum

class Button:
  def __init__(self, name, action=lambda: None, hold_time=0):
    self.name = name
    self.action = action
    self.hold_time = hold_time
    self.timer = 0
    self.is_down = False

  def update(self, dt, is_down, is_pressed=False):
    if is_pressed:
      self.is_down = True
    elif not is_down:
      self.is_down = False
    if self.is_down:
      if self.timer >= 0:
        self.timer += dt
        if self.timer >= self.hold_time:
          self.action()
          self.timer = -1
    else:
      self.timer = 0
    
class State:

  def __init__(self):
    self.app = None
    self.buttons = [
      Button("Left"),
      Button("Middle"),
      Button("Right")
    ]
    
  def begin(self):
    self.app.input.bind(pygame.K_z, pressed=lambda: self.buttons[0].action())
    self.app.input.bind(pygame.K_x, pressed=lambda: self.buttons[1].action())
    self.app.input.bind(pygame.K_c, pressed=lambda: self.buttons[2].action())

  def process_input(self):
    pass

  def update(self, dt):
    pass

  def draw(self, g):
    w, h = self.app.screen.get_size()
    center_x = w / 2
    center_y = h - 40
    for index, button in enumerate(self.buttons):
      #x = center_x + (index - 1) * 200
      #y = h - 40
      #self.app.draw_text_box("", x, y, 100, 40)
      #self.app.draw_text_box(x, y, button.name, align=Align.Centered, color=BLACK)
      text_width, text_height = g.font.size(button.name)
      r = pygame.Rect(center_x, center_y, 0, 0)
      r.inflate_ip(text_width, text_height)
      r.inflate_ip(16, 10)
      r.x += (index - 1) * 200
      g.fill_rect(r.x, r.y, r.width, r.height, color=LIGHT_GRAY)
      if button.is_down and button.hold_time > 0 and button.timer > 0:
        percent = button.timer / button.hold_time
        g.fill_rect(r.x, r.y, r.width * percent, r.height, color=YELLOW)
      g.draw_rect(r.x, r.y, r.width, r.height, thickness=2, color=BLACK)
      g.draw_text(r.x + (r.width / 2), r.y + (r.height / 2), button.name, align=Align.Centered, color=BLACK)

