
from enum import IntEnum
import os
import pygame
import random
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_cards.state import *

class CardSide(IntEnum):
  Front = 0
  Back = 1

class Card:
  def __init__(self, front, back):
    self.text = [front, back]
    self.marked = False
    self.encountered = False
    self.age = 0
  
class CardSet:
  def __init__(self, cards=()):
    self.name = "Untitled"
    self.path = ""
    self.cards = list(cards)
    self.card_count = len(cards)

  def load(self, path):
    self.path = path
    self.cards = []
    self.header_dict = {"name": os.path.splitext(os.path.basename(path))[0],
                        "side": "english"}
    with open(path, "r", encoding="utf8") as f:
      header = True
      for line in f:
        line = line.strip()
        if header and "=" in line:
          key, value = [t.strip() for t in line.split("=")]
          if key in self.header_dict:
            self.header_dict[key] = value
          else:
            raise KeyError(key)
        else:
          header = False
          if "-" in line:
            tokens = [t.strip() for t in line.split("-")]
            if len(tokens) == 2:
              card = Card(tokens[0], tokens[1])
              self.cards.append(card)

    self.name = self.header_dict["name"]
    self.side = CardSide.Front if self.header_dict["side"] == "russian" else CardSide.Back
    self.card_count = len(self.cards)

  def next(self):
    index = random.randint(0, len(self.cards) - 1)
    card = self.cards[index]
    del self.cards[index]
    return card

class StudyState(State):
  def __init__(self, path):
    super().__init__()
    self.card_font = pygame.font.Font(None, 72)
    self.path = path
    self.name = os.path.basename(self.path)
    self.shown_side = CardSide.Back
    self.hidden_side = CardSide.Front
    self.encountered_cards = []
    self.card = None
    self.revealed = False
    self.card_set = None

  def begin(self):
    self.buttons[0] = Button("Reveal", self.reveal)
    self.buttons[1] = Button("Exit", self.app.pop_state, hold_time=0.7)
    self.buttons[2] = Button("Next", self.next)

    self.encountered_cards = []
    self.card = None
    self.revealed = False
    self.card_set = CardSet()
    self.card_set.load(os.path.join(self.app.root, self.path))
    self.shown_side = self.card_set.side
    self.hidden_side = CardSide(1 - self.card_set.side)
    self.next_card()

  def exit_to_menu(self):
    self.app.quit()

  def next(self):
    self.card.marked = False
    self.next_card()
  
  def mark(self):
    self.card.marked = True
    self.next_card()

  def next_card(self):
    self.revealed = False
    self.buttons[0] = Button("Reveal", self.reveal)

    for card in self.encountered_cards:
      card.age += 1

    if len(self.card_set.cards) > 0:
      self.card = self.card_set.next()
    else:
      choices = []
      total_odds = 0
      for index, card in enumerate(self.encountered_cards):
        odds = card.age - min(len(self.encountered_cards) / 2, 4)
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
      self.card = self.encountered_cards[picked_index]
      del self.encountered_cards[picked_index]
    
    self.encountered_cards.insert(0, self.card)
    self.card.age = 0
    self.card.encountered = True

  def reveal(self):
    self.revealed = True
    self.buttons[0] = Button("Mark", self.mark)

  def draw(self, g):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2

    marked_count = len([x for x in self.encountered_cards if not x.marked])
    g.draw_text(32, 32,
                text=self.card_set.name,
                color=GRAY,
                align=Align.TopLeft)
    g.draw_text(screen_width - 32, 32,
                text="{} / {} / {}".format(marked_count,
                                           len(self.encountered_cards),
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
    #text = "[" + ", ".join("{}.{}.{}".format(c.front, c.age, c.marked) for c in self.encountered_cards) + "]"
    #g.draw_text(32, 330, text)

