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
from study_tool.menu import Menu
from study_tool.state import *
from study_tool.sub_menu_state import SubMenuState
from study_tool.scheduler import ScheduleMode

class MenuState(State):
  def __init__(self, package):
    super().__init__()
    self.package = package
    self.buttons[0] = Button("Up")
    self.buttons[1] = Button("Select", self.select)
    self.buttons[2] = Button("Down")
    self.title = None
    self.top_level = package.parent == None
    self.title_font = pygame.font.Font(None, 50)
    self.option_font = pygame.font.Font(None, 42)
    self.option_spacing = 40
    self.option_margin = 48
    self.option_border_thickness = 4
    self.menu = None

  def begin(self):
    self.title = (self.app.title if self.package.parent is None
                  else self.package.name)

    screen_width, screen_height = self.app.screen.get_size()
    viewport = pygame.Rect(0, self.margin_top, screen_width,
                           screen_height - self.margin_top - self.margin_bottom)

    # Create menu options
    self.menu = Menu(options=[], viewport=viewport)
    self.menu.draw_menu_option_text = self.draw_menu_option_text
    back_option = "Quit" if self.top_level else "Back"
    self.menu.options = [(back_option, self.app.pop_state)]
    for package in self.package.packages:
      self.menu.options.append(("[...] {}".format(package.name), package))
    for card_set in self.package.card_sets:
      self.menu.options.append((card_set.name, card_set))
    self.menu.options.append(("Study all " + self.package.name, self.package))
      
  def open_set(self, card_set):
    options = [("Quiz English", lambda: self.app.push_study_state(card_set, CardSide.English)),
               ("Quiz Russian", lambda: self.app.push_study_state(card_set, CardSide.Russian))]
    options += [("Quiz New Cards", lambda: self.app.push_study_state(card_set,
                                                                      side=CardSide.English,
                                                                      mode=ScheduleMode.NewOnly))]
    options += [("Quiz Problem Cards", lambda: self.app.push_study_state(
      card_set=card_set.get_problem_cards(), side=CardSide.English))]
    options += [("List", lambda: self.app.push_card_list_state(card_set)),
                ("Cancel", None)]
    self.app.push_state(SubMenuState(card_set.name, options))

  def select(self):
    option, action = self.menu.selected_option()
    if isinstance(action, CardSetPackage):
      if action == self.package:
        self.open_set(action)
      else:
        self.app.push_state(MenuState(action))
    elif isinstance(action, CardSet):
      self.open_set(action)
    else:
      action()

  def update(self, dt):
    self.menu.update_menu(app=self.app, dt=dt)

  def draw_menu_option_text(self, g, option, rect, highlighted):
    name, value = option
    if highlighted:
      text_color = Config.option_highlighted_text_color
    else:
      text_color = Config.option_text_color

    # Draw the option name
    center_y = rect.y + (rect.height / 2)
    g.draw_text(rect.x + 16, center_y,
                text=name, font=self.option_font,
                color=text_color, align=Align.MiddleLeft)

    # Draw the completion bar
    if isinstance(value, CardSet) or isinstance(value, CardSetPackage):
      self.app.draw_completion_bar(
        g, center_y, int(rect.x + (rect.width * 0.6)),
        rect.x + rect.width - 16, value)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    
    # Draw the list of menu options
    self.menu.draw_menu(g)

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

    metrics = self.package.get_study_metrics()
    g.draw_text(screen_center_x, self.margin_top / 2,
                text="{:.0f} / {:.0f}".format(metrics.get_proficiency_count(),
                                              metrics.history_score),
                font=self.title_font,
                color=Config.title_color,
                align=Align.Centered)

    # Draw completion progress
    self.app.draw_completion_bar(
      g, self.margin_top / 2,
      max(screen_width * 0.6, title_right + 32),
      screen_width - 32,
      self.package)
    