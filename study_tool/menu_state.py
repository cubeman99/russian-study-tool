from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg import math
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.config import Config
from study_tool.card import CardSide
from study_tool.card_set import CardSet, CardSetPackage
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
    self.option_spacing = 40
    self.option_margin = 48
    self.scroll_position = 0.0
    self.option_border_thickness = 4

  def begin(self):
    # Create menu options
    count = sum(s.card_count for s in self.package.all_card_sets())
    self.title = (self.app.title if self.package.parent is None
                  else self.package.name)
    self.cursor = 1.0 if self.top_level else 0.0

    back_option = "Quit" if self.top_level else "Back"
    self.options = [(back_option, self.app.pop_state)]
    for package in self.package.packages:
      self.options.append(("[...] {}".format(package.name), package))
    for card_set in self.package.card_sets:
      self.options.append((card_set.name, card_set))

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
    if isinstance(action, CardSetPackage):
      self.app.push_state(MenuState(action))
    elif isinstance(action, CardSet):
      self.open_set(action)
    else:
      action()

  def update(self, dt):
    move = self.app.inputs[2].get_amount() - self.app.inputs[0].get_amount()
    speed = 10.0
    self.cursor += move * dt * speed
    if self.cursor < 0.5:
      self.cursor += len(self.options)
    if self.cursor > len(self.options) - 0.5:
      self.cursor -= len(self.options)
      
    _, screen_height = self.app.screen.get_size()
    option_list_height = len(self.options) * self.option_spacing
    option_area_height = (screen_height - self.margin_top - self.margin_bottom)
    if option_list_height > option_area_height:
      scrolling = True
      desired_scroll_position = (((self.cursor + 0.5) * self.option_spacing) -
                                 option_area_height / 2)
      desired_scroll_position = max(0, desired_scroll_position)
      desired_scroll_position = min(desired_scroll_position,
                                    option_list_height - option_area_height)
      self.scroll_position = cmg.math.lerp(
        self.scroll_position,
        desired_scroll_position,
        0.2)
      if abs(self.scroll_position - desired_scroll_position) < 2:
        self.scroll_position = desired_scroll_position

  def draw_option_list(self, g, top):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    option_index = int(round(self.cursor))
    option_top = self.margin_top + top
    row_width = screen_width - (self.option_margin * 2)
    border_row_width = row_width + (self.option_border_thickness * 2)

    # Draw the cursor
    cursor_y = option_top + ((self.cursor + 0.5) * self.option_spacing)
    g.fill_rect(self.option_margin - self.option_border_thickness - Config.option_cursor_width,
                cursor_y - (Config.option_cursor_height / 2),
                border_row_width + (Config.option_cursor_width * 2),
                Config.option_cursor_height,
                color=Config.option_cursor_color)
    
    # Draw menu options
    for index, (option, value) in enumerate(self.options):
      y = option_top + (index * self.option_spacing)
      center_y = y + (self.option_spacing / 2)

      if index == option_index:
        text_color = Config.option_highlighted_text_color
        row_color = Config.option_highlighted_background_color
        border_color = Config.option_highlighted_border_color
      else:
        text_color = Config.option_text_color
        row_color = Config.option_background_colors[index % 2]
        border_color = Config.option_border_colors[index % 2]

      # Draw the option border
      g.fill_rect(self.option_margin - self.option_border_thickness, y,
                  border_row_width, self.option_spacing, color=border_color)
      if index == len(self.options) - 1:
        g.fill_rect(self.option_margin - self.option_border_thickness,
                    y + self.option_spacing, border_row_width,
                    self.option_border_thickness, color=border_color)

      # Draw the row background
      g.fill_rect(self.option_margin, y, row_width,
                  self.option_spacing, color=row_color)

      # Draw the option name
      g.draw_text(self.option_margin + 16, center_y,
                  text=option, font=self.option_font,
                  color=text_color, align=Align.MiddleLeft)

      # Draw the completion bar
      if isinstance(value, CardSet) or isinstance(value, CardSetPackage):
        self.app.draw_completion_bar(
          g, center_y, int(screen_width * 0.6),
          screen_width - self.option_margin - 16, value)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    
    # Draw the list of menu options
    self.draw_option_list(g, -self.scroll_position)

    # Draw the state
    State.draw(self, g)

    # Draw title
    title_left = self.option_margin
    title_right = title_left + g.measure_text(text=self.title,
                                              font=self.title_font)[0]
    g.draw_text(title_left, self.margin_top / 2,
                text=self.title,
                font=self.title_font,
                color=Config.title_color,
                align=Align.MiddleLeft)

    # Draw completion progress
    self.app.draw_completion_bar(
      g, self.margin_top / 2,
      max(screen_center_x, title_right + 32),
      screen_width - 32,
      self.package)
    