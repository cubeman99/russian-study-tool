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
from study_tool.menu import Menu
from study_tool.state import *
from study_tool.sub_menu_state import SubMenuState

class CardListState(State):
  def __init__(self, card_set):
    super().__init__()
    self.card_set = card_set

    self.card_font = pygame.font.Font(None, 30)
    self.line_spacing = 30
    self.row_colors = [color.WHITE,
                       color.gray(230)]
    self.menu = None
    self.row_marked_color = color.rgb(255, 200, 200)
    self.row_unmarked_color = color.rgb(200, 255, 200)
    self.row_unseen_color = color.make_gray(230)

  def begin(self):
    self.buttons[0] = Button("Scroll Up")
    self.buttons[1] = Button("Menu", self.pause)
    self.buttons[2] = Button("Scroll Down")

    screen_width, screen_height = self.app.screen.get_size()
    viewport = pygame.Rect(0, self.margin_top, screen_width,
                           screen_height - self.margin_top - self.margin_bottom)

    self.menu = Menu(options=self.card_set.cards, viewport=viewport)
    self.menu.option_margin = 4
    self.menu.draw_menu_option_text = self.draw_menu_option_text
    self.menu.get_option_background_color = self.get_option_background_color

    g = self.app.graphics
    self.max_column_width = 0
    for card in self.card_set.cards:
      self.max_column_width = max(self.max_column_width,
                                  g.measure_text(card.russian, font=self.card_font)[0])

  def pause(self):
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("Quiz English", lambda: (self.app.pop_state,
                                 self.app.push_study_state(self.card_set, CardSide.English))),
       ("Quiz Russian", lambda: (self.app.pop_state,
                                 self.app.push_study_state(self.card_set, CardSide.Russian))),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def update(self, dt):
    self.menu.update_menu(app=self.app, dt=dt)
    
  def get_option_background_color(self, index, card, highlighted):
    #if highlighted:
    #  return Config.option_highlighted_background_color
    #else:
    if not card.encountered:
      row_color = self.row_unseen_color
    elif card.marked:
      row_color = self.row_marked_color
    else:
      row_color = self.row_unmarked_color
    if index % 2 == 1:
      row_color *= 0.94
    if highlighted:
      row_color = math.lerp(row_color, color.WHITE, 0.5)
    return row_color

  def draw_menu_option_text(self, g, option, rect, highlighted):
    card = option
    if highlighted:
      text_color = Config.option_highlighted_text_color
    else:
      text_color = Config.option_text_color

    column_1_x = rect.x + 32
    column_2_x = max(rect.x + 32 + self.max_column_width + 16,
                     rect.x + (rect.width / 2) + 32)
    center_y = rect.y + (rect.height / 2)

    g.draw_text(column_1_x, center_y,
                text=card.russian, font=self.card_font,
                color=text_color, align=Align.MiddleLeft)
    g.draw_text(column_2_x, center_y,
                text=card.english, font=self.card_font,
                color=text_color, align=Align.MiddleLeft)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    
    #max_column_width = 0
    #for card in self.card_set.cards:
    #  max_column_width = max(max_column_width,
    #                         g.measure_text(card.russian, font=self.card_font)[0])

    ## Draw cards
    #column_1_x = 32
    #column_2_x = max(32 + max_column_width + 16,
    #                 screen_center_x + 32)
    #y = self.margin_top + int(round(self.scroll_position * self.line_spacing))
    #for index, card in enumerate(self.card_set.cards):
    #  row_color = self.row_colors[index % 2]

    #  if not card.encountered:
    #    row_color = self.row_unseen_color
    #  elif card.marked:
    #    row_color = self.row_marked_color
    #  else:
    #    row_color = self.row_unmarked_color
    #  if index % 2 == 1:
    #    row_color *= 0.94

    #  g.fill_rect(0, y,
    #              screen_width, self.line_spacing,
    #              color=row_color)
    #  g.draw_text(column_1_x, y + (self.line_spacing / 2),
    #              text=card.russian,
    #              font=self.card_font,
    #              color=color.BLACK,
    #              align=Align.MiddleLeft)
    #  g.draw_text(column_2_x, y + (self.line_spacing / 2),
    #              text=card.english,
    #              font=self.card_font,
    #              color=color.BLACK,
    #              align=Align.MiddleLeft)
    #  y += self.line_spacing
      
    # Draw the list of menu options
    self.menu.draw_menu(g)

    # Draw state
    State.draw(self, g)

    # Draw title
    g.draw_text(32, self.margin_top / 2,
                text=self.card_set.name,
                color=Config.title_color,
                align=Align.MiddleLeft)
    self.app.draw_completion_bar(g, self.margin_top / 2,
                                 screen_center_x - 80,
                                 screen_width - 32,
                                 self.card_set)
