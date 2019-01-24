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

class MenuState(State):
  def __init__(self, local_path):
    super().__init__()
    self.local_path = local_path
    self.buttons[0] = Button("Up")
    self.buttons[1] = Button("Select", self.select)
    self.buttons[2] = Button("Down")
    self.cursor = 0.0
    self.options = []
    self.title = None
    self.top_level = False
    self.title_font = pygame.font.Font(None, 50)
    self.option_font = pygame.font.Font(None, 42)

  def begin(self):
    # Create menu options
    self.top_level = (len(self.app.states) == 1)
    self.title = self.app.title if self.top_level else os.path.basename(self.local_path)
    back_option = "Quit" if self.top_level else "Back"
    self.options = [(back_option, self.app.pop_state)]
    dir_options = []
    card_sets = []
    for name in os.listdir(self.app.root + "/" + self.local_path):
      path = os.path.join(self.local_path, name)
      full_path = os.path.join(self.app.root, path)
      if os.path.isdir(full_path):
        dir_options.append(("[" + name + "]", self.open_directory_lambda(path)))
      elif os.path.isfile(full_path) and path.endswith(".txt"):
        card_sets += load_card_set_file(full_path)
    self.options += sorted(dir_options)
    for card_set in card_sets:
      self.options.append(("{} [{}]".format(card_set.name, card_set.card_count),
                           self.open_set_lambda(card_set)))
    self.cursor = 1.0 if self.top_level else 0.0

  def open_directory_lambda(self, path):
    return lambda: self.app.push_state(MenuState(path))
  
  def open_set_lambda(self, card_set):
    return lambda: self.app.push_state(StudyState(card_set))

  def select(self):
    option_index = int(round(self.cursor))
    option, action = self.options[option_index]
    action()

  def update(self, dt):
    move = self.app.inputs[2].get_amount() - self.app.inputs[0].get_amount()
    speed = 10.0
    self.cursor += move * dt * speed
    if self.cursor < 0.5:
      self.cursor += len(self.options)
    if self.cursor > len(self.options) - 0.5:
      self.cursor -= len(self.options)

  def draw(self, g):
    title = os.path.dirname(self.local_path)
    if title != "":
      title += " - "
    title += self.title
    g.draw_text(64, 48,
                text=title,
                font=self.title_font,
                color=BLACK)

    row_count = 8
    option_index = int(round(self.cursor))
    x = 0
    y = 0
    max_width = 0
    for index, (option, _) in enumerate(self.options):
      text_width, _ = self.option_font.size("> " + option)
      if index == option_index:
        color = BLUE
        g.draw_text(64 + x, 128 + y,
                    text="> ",
                    font=self.option_font,
                    color=color,
                    align=Align.TopRight)
      else:
        color = BLACK
      g.draw_text(64 + x, 128 + y,
                  text=option,
                  font=self.option_font,
                  color=color)
      max_width = max(max_width, text_width)
      if (index + 1) % row_count == 0:
        x += max_width + 50
        y = 0
      else:
        y += 44

    State.draw(self, g)
    