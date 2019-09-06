from enum import IntEnum
import os
import pygame
import random
import time
from cmg import color
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import *
from study_tool.card_set import *
from study_tool.entities.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState

class ReadTextState(State):
  def __init__(self):
    super().__init__()

  def begin(self):
    self.buttons[0] = Button("Scroll Up")
    self.buttons[1] = Button("Menu", self.pause)
    self.buttons[2] = Button("Scroll Down")

  def pause(self):
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def update(self, dt):
    pass
    
  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    
    # Draw state
    State.draw(self, g)
