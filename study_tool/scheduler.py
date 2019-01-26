from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import *
from study_tool.card_set import *
from study_tool.config import Config

def choose_weighted(cards, key=lambda card: 1):
  if len(cards) == 0:
    return None
  total_odds = 0
  for index, card in enumerate(cards):
    odds = key(card)
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
  return cards[picked_index]

def choose(cards):
  if len(cards) == 0:
    return None
  return cards[random.randint(0, len(cards) - 1)]

class Scheduler:
  def __init__(self, cards):
    self.new_cards = [c for c in cards if c.proficiency_level == 0]
    self.cards = [c for c in cards if c.proficiency_level > 0]
    for card in self.cards:
      card.rep = -card.age
    self.proficiency_levels = Config.proficiency_levels
    self.proficiency_level_intervals = Config.proficiency_level_intervals
    self.new_card_interval = Config.new_card_interval
    self.rep = 0

  def mark(self, card: Card, knew_it: bool):
    if card in self.new_cards:
      card.proficiency_level = 2 if knew_it else 1
      del self.new_cards[self.new_cards.index(card)]
      self.cards.append(card)
    elif knew_it:
      card.proficiency_level = min(card.proficiency_level + 1,
                                   self.proficiency_levels)
    else:
      card.proficiency_level = max(1, card.proficiency_level - 1)
    card.rep = self.rep
    card.marked = not knew_it
    card.last_encounter_time = time.time()

  def next(self) -> Card:
    card = self._get_next_card()
    self.rep += 1
    for c in self.cards:
      c.age = self.rep - c.rep
    return card

  def _get_next_card(self) -> Card:
    card = None

    if self.rep % self.new_card_interval == 0:
      card = self._get_new_card()
      if card is not None:
        return card

    available = [c for c in self.cards if
                 self.rep - c.rep >= self.proficiency_level_intervals[c.proficiency_level]]
    card = choose(available)
    if card is not None:
      return card
      
    card = self._get_new_card()
    if card is not None:
      return card
    
    for offset in range(1, self.proficiency_levels):
      available = [c for c in self.cards if
                   self.rep - c.rep >= self.proficiency_level_intervals[
                     max(1, c.proficiency_level - offset)]]
      card = choose(available)
      if card is not None:
        return card

    card = choose(self.cards)
    if card is not None:
      return card

    return None

  def _get_new_card(self) -> Card:
    if len(self.new_cards) == 0:
      return None
    card = choose(self.new_cards)
    card.rep = self.rep
    return card

