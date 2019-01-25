from enum import IntEnum
import os
import pygame
import random
import time
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.state import *
from study_tool.study_state import *

class SubMenuState(State):
  def __init__(self, title, options=()):
    super().__init__()
    self.draw_state_below = True
    self.title = title
    self.options = list(options)
    self.cursor = 0.0
    self.width = None
    self.height = None
    self.title_font = pygame.font.Font(None, 50)
    self.option_font = pygame.font.Font(None, 42)
    self.background_color = WHITE
    self.border_color = BLACK
    self.title_color = BLACK

  def begin(self):
    self.cursor = 0.0
    self.buttons[0] = Button("Up")
    self.buttons[1] = Button("Select", self.select)
    self.buttons[2] = Button("Down")

  def select(self):
    option_index = int(round(self.cursor))
    option, action = self.options[option_index]
    self.app.pop_state()
    if action is not None:
      action()

  def update(self, dt):
    move = self.app.inputs[2].get_amount() - self.app.inputs[0].get_amount()
    if abs(move) > 0.01:
      speed = 10.0
      self.cursor += move * dt * speed
      if self.cursor < 0.5:
        self.cursor += len(self.options)
      if self.cursor > len(self.options) - 0.5:
        self.cursor -= len(self.options)
    else:
      self.cursor = round(self.cursor)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2

    width = self.width
    height = self.height
    
    if self.width is None:
      width = 32 + (16 * (len(self.options) - 1))
      for option, _ in self.options:
        width += self.option_font.size(option)[0]
    if self.height is None:
      height = 32 + self.option_font.size(option)[1]
      height += 16 + self.title_font.size(self.title)[1]
    
    rect = pygame.Rect(screen_center_x - (width / 2),
                       screen_center_y - (height / 2),
                       width, height)

    # Draw the menu box
    g.fill_rect(rect, color=self.background_color)
    g.draw_rect(rect, color=self.border_color, thickness=4)

    # Draw the title
    g.draw_text(x=screen_center_x, y=rect.y + 16,
                text=self.title,
                font=self.title_font,
                color=self.title_color,
                align=Align.TopCenter)


    row_count = 8
    option_index = int(round(self.cursor))
    x = rect.x + 16
    y = rect.y + rect.height - 16
    for index, (option, _) in enumerate(self.options):
      option_width, option_height = self.option_font.size(option)
      color = BLACK
      button_rect = pygame.Rect(x, y - option_height, option_width, option_height)
      button_rect.inflate_ip(8, 8)
      button_back_color = self.background_color
      if index == option_index:
        button_back_color = YELLOW
      g.fill_rect(button_rect, color=button_back_color)
      g.draw_rect(button_rect, color=self.border_color, thickness=2)
      g.draw_text(x, y,
                  text=option,
                  font=self.option_font,
                  color=color,
                  align=Align.BottomLeft)
      if index == option_index:
        t = self.cursor - option_index + 0.5
        tx = x + (option_width * t) - 2
        g.fill_rect(tx, y, 4, 8, color=BLUE)


      x += option_width + 16
    