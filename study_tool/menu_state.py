from enum import IntEnum
import os
import pygame
import random
import time
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.card import CardSide
from study_tool.state import *
from study_tool.sub_menu_state import SubMenuState

class MenuState(State):
  def __init__(self, package):
    super().__init__()
    self.package = package
    self.buttons[0] = Button("Up")
    self.buttons[1] = Button("Select", self.select)
    self.buttons[2] = Button("Down")
    self.cursor = 0.0
    self.options = []
    self.title = None
    self.top_level = package.parent == None
    self.title_font = pygame.font.Font(None, 50)
    self.option_font = pygame.font.Font(None, 42)

  def begin(self):
    # Create menu options
    count = sum(s.card_count for s in self.package.all_card_sets())
    self.title = self.app.title if self.package.parent is None else self.package.name
    self.title = "[{}] {}".format(count, self.title)
    self.cursor = 1.0 if self.top_level else 0.0

    back_option = "Quit" if self.top_level else "Back"
    self.options = [(back_option, self.app.pop_state)]
    for package in self.package.packages:
      count = sum(s.card_count for s in package.all_card_sets())
      self.options.append(("[{}] **{}**".format(count, package.name),
                           self.open_directory_lambda(package)))
    for card_set in self.package.card_sets:
      self.options.append(("[{}] {}".format(card_set.card_count, card_set.name),
                           self.open_set_lambda(card_set)))

  def open_directory_lambda(self, package):
    return lambda: self.app.push_state(MenuState(package))
  
  def open_set_lambda(self, card_set):
    return lambda: self.open_set(card_set)

  def open_set(self, card_set):
    self.app.push_state(SubMenuState(
      card_set.name,
      [("Quiz En", lambda: self.app.push_study_state(card_set, CardSide.English)),
       ("Quiz Ru", lambda: self.app.push_study_state(card_set, CardSide.Russian)),
       ("List", lambda: self.app.push_card_list_state(card_set)),
       ("Cancel", None)]))

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

    # Draw title
    g.draw_text(64, self.margin_top / 2,
                text=self.title,
                font=self.title_font,
                color=BLACK,
                align=Align.MiddleLeft)
    