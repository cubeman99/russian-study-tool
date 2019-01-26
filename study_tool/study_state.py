from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import Card, CardSide
from study_tool.card_set import CardSet, CardSetPackage
from study_tool.config import Config
from study_tool.scheduler import Scheduler
from study_tool.state import State, Button
from study_tool.sub_menu_state import SubMenuState

class StudyState(State):
  def __init__(self, card_set, side=CardSide.English):
    super().__init__()
    self.card_font = pygame.font.Font(None, 72)
    self.card_status_font = pygame.font.Font(None, 30)
    self.card_set = card_set
    self.path = card_set.path
    self.name = os.path.basename(self.path)
    self.shown_side = side
    self.hidden_side = CardSide(1 - side)
    self.card = None
    self.revealed = False
    self.scheduler = None

  def begin(self):
    self.buttons[0] = Button("Reveal", self.reveal)
    self.buttons[1] = Button("Exit", self.pause)
    self.buttons[2] = Button("Next", self.next)

    self.scheduler = Scheduler(self.card_set.cards)
    self.seen_cards = []
    self.card = None
    self.revealed = False
    self.next_card()

  def switch_sides(self):
    self.shown_side = CardSide(1 - self.shown_side)
    self.hidden_side = CardSide(1 - self.shown_side)
    
  def pause(self):
    other_side = CardSide(1 - self.shown_side)
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("List", lambda: (self.app.pop_state(),
                         self.app.push_card_list_state(self.card_set))),
       ("Quiz " + other_side.name, self.switch_sides),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def exit_to_menu(self):
    self.app.quit()

  def next(self):
    self.scheduler.mark(self.card, knew_it=True)
    self.app.save()
    self.next_card()
  
  def mark(self):
    self.scheduler.mark(self.card, knew_it=False)
    self.app.save()
    self.next_card()

  def next_card(self):
    self.revealed = False
    self.buttons[0] = Button("Reveal", self.reveal)
    self.card = self.scheduler.next()

  def reveal(self):
    self.revealed = True
    self.buttons[0] = Button("Mark", self.mark)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2

    if self.card.proficiency_level > 0:
      marked_state_color = math.lerp(Config.proficiency_level_colors[
        self.card.proficiency_level], color.WHITE, 0.7)
      g.fill_rect(0, self.margin_top, screen_width, 32,
                  color=marked_state_color)
      g.fill_rect(0, screen_height - self.margin_bottom - 32,
                  screen_width, 32,
                  color=marked_state_color)
      g.draw_text(screen_width - 16, self.margin_top + (32 / 2),
                  text=self.card.elapsed_time_string(),
                  align=Align.MiddleRight,
                  color=marked_state_color * 0.7,
                  font=self.card_status_font)
    
    # Draw card text
    g.draw_text(screen_center_x, screen_center_y - 50,
                text=self.card.text[self.shown_side],
                font=self.card_font,
                color=Config.card_front_text_color,
                align=Align.Centered)
    if self.revealed:
      g.draw_text(screen_center_x, screen_center_y + 50,
                  text=self.card.text[self.hidden_side],
                  font=self.card_font,
                  color=Config.card_back_text_color,
                  align=Align.Centered)
      
    # Draw state
    State.draw(self, g)

    # Draw text at top
    marked_count = len([x for x in self.card_set.cards if not x.marked])
    g.draw_text(32, self.margin_top / 2,
                text=self.card_set.name,
                color=cmg.color.GRAY,
                align=Align.MiddleLeft)
    self.app.draw_completion_bar(g, self.margin_top / 2,
                                 screen_center_x - 80,
                                 screen_width - 32,
                                 self.card_set)
