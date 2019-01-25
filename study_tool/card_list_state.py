from enum import IntEnum
import os
import pygame
import random
import time
from cmg import color
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import *
from study_tool.card_set import *
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
    self.scroll_speed = 35.0  # rows per second

    self.row_marked_color = color.rgb(255, 200, 200)
    self.row_unmarked_color = color.rgb(200, 255, 200)
    self.row_unseen_color = color.make_gray(230)

  def begin(self):
    self.buttons[0] = Button("Scroll Up")
    self.buttons[1] = Button("Menu", self.pause)
    self.buttons[2] = Button("Scroll Down")
    self.scroll_position = 0

  def pause(self):
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("Quiz En", lambda: (self.app.pop_state,
                            self.app.push_study_state(self.card_set, CardSide.English))),
       ("Quiz Ru", lambda: (self.app.pop_state,
                            self.app.push_study_state(self.card_set, CardSide.Russian))),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def update(self, dt):
    move = self.app.inputs[0].get_amount() - self.app.inputs[2].get_amount()
    if abs(move) > 0.01:
      self.scroll_position += move * self.scroll_speed * dt
      self.scroll_position = max(self.scroll_position, -len(self.card_set.cards) + 8)
      self.scroll_position = min(0, self.scroll_position)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    
    max_column_width = 0
    for card in self.card_set.cards:
      max_column_width = max(max_column_width,
                             g.measure_text(card.russian, font=self.card_font)[0])

    # Draw cards
    column_1_x = 32
    column_2_x = max(32 + max_column_width + 16,
                     screen_center_x + 32)
    y = self.margin_top + int(round(self.scroll_position * self.line_spacing))
    for index, card in enumerate(self.card_set.cards):
      row_color = self.row_colors[index % 2]

      if not card.encountered:
        row_color = self.row_unseen_color
      elif card.marked:
        row_color = self.row_marked_color
      else:
        row_color = self.row_unmarked_color
      if index % 2 == 1:
        row_color *= 0.94

      g.fill_rect(0, y,
                  screen_width, self.line_spacing,
                  color=row_color)
      g.draw_text(column_1_x, y + (self.line_spacing / 2),
                  text=card.russian,
                  font=self.card_font,
                  color=color.BLACK,
                  align=Align.MiddleLeft)
      g.draw_text(column_2_x, y + (self.line_spacing / 2),
                  text=card.english,
                  font=self.card_font,
                  color=color.BLACK,
                  align=Align.MiddleLeft)
      y += self.line_spacing

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
