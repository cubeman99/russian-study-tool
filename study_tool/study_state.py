from enum import IntEnum
import os
import pygame
import random
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card_set import *
from study_tool.state import *
from study_tool.sub_menu_state import *

class StudyState(State):
  def __init__(self, card_set, side=CardSide.English):
    super().__init__()
    self.card_font = pygame.font.Font(None, 72)
    self.card_set = card_set
    self.path = card_set.path
    self.name = os.path.basename(self.path)
    self.shown_side = side
    self.hidden_side = CardSide(1 - side)
    self.seen_cards = []
    self.card = None
    self.revealed = False

  def begin(self):
    self.buttons[0] = Button("Reveal", self.reveal)
    self.buttons[1] = Button("Exit", self.pause)
    self.buttons[2] = Button("Next", self.next)

    self.unseen_cards = list(self.card_set.cards)
    self.seen_cards = []
    self.card = None
    self.revealed = False
    self.next_card()

  def switch_sides(self):
    self.shown_side = CardSide(1 - self.shown_side)
    self.hidden_side = CardSide(1 - self.shown_side)
    
  def pause(self):
    other_side = CardSide(1 - self.shown_side)
    other_side_name = "En" if other_side == CardSide.English else "Ru"
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("List", None),
       ("Quiz " + other_side_name, self.switch_sides),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def exit_to_menu(self):
    self.app.quit()

  def next(self):
    self.card.skip()
    self.app.save()
    self.next_card()
  
  def mark(self):
    self.card.mark()
    self.app.save()
    self.next_card()

  def next_card(self):
    self.revealed = False
    self.buttons[0] = Button("Reveal", self.reveal)

    for card in self.seen_cards:
      card.age += 1

    if len(self.card_set.cards) > 0:
      self.card = self.card_set.next(seen=self.seen_cards,
                                     unseen=self.unseen_cards)
    else:
      choices = []
      total_odds = 0
      for index, card in enumerate(self.seen_cards):
        odds = card.age - min(len(self.seen_cards) / 2, 4)
        odds *= odds
        if card.marked:
          odds *= odds
        total_odds += odds
        choices.append((total_odds, index))
      odds_index = random.randint(0, total_odds - 1)
      picked_index = None
      for odds, index in choices:
        if odds_index < odds:
          picked_index = index
          break
      self.card = self.seen_cards[picked_index]
      del self.seen_cards[picked_index]
    
    self.seen_cards.insert(0, self.card)
    self.card.encounter()

  def reveal(self):
    self.revealed = True
    self.buttons[0] = Button("Mark", self.mark)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2

    marked_count = len([x for x in self.card_set.cards if not x.marked])
    g.draw_text(32, 32,
                text=self.card_set.name,
                color=GRAY,
                align=Align.TopLeft)
    g.draw_text(screen_width - 32, 32,
                text="{} / {} / {}".format(marked_count,
                                           len(self.seen_cards),
                                           self.card_set.card_count),
                color=GRAY,
                align=Align.TopRight)
    g.draw_text(screen_center_x, screen_center_y - 50,
                text=self.card.text[self.shown_side],
                font=self.card_font,
                color=BLACK,
                align=Align.Centered)
    if self.revealed:

      g.draw_text(screen_center_x, screen_center_y + 50,
                  text=self.card.text[self.hidden_side],
                  font=self.card_font,
                  color=BLACK,
                  align=Align.Centered)
    State.draw(self, g)
