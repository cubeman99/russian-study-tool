import os
import random
import re
import time
from study_tool.card import Card, CardSide, SourceLocation
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config


class StudySet:
  def __init__(self, name="", cards=()):
    self.name = name
    self.cards = list(cards)

  def get_problem_cards(self):
    cs = sorted(self.cards, key=lambda c: c.get_history_score())
    for c in reversed(cs):
      history_preview_len = 16
      history_preview = ""
      for i in range(min(history_preview_len, len(c.history))):
        history_preview += "." if c.history[i] else "x"
      history_preview += " " * (history_preview_len - len(history_preview))
      print("{:.4f} : {:3} [{}] {}".format(c.get_history_score(),
                                           len(c.history),
                                           history_preview,
                                           c.russian,
                                           c.english))
    return StudySet(name=self.name,
                    cards=[c for c in self.cards
                           if len(c.history) < 5
                           or c.get_history_score() < 0.9])

class CardSet(StudySet):
  def __init__(self, cards=()):
    StudySet.__init__(self, name="Untitled", cards=cards)
    self.key = None
    self.path = ""
    self.info = ""
    self.side = CardSide.English
    self.source = None

  def next(self, seen, unseen):
    index = random.randint(0, len(unseen) - 1)
    card = unseen[index]
    del unseen[index]
    return card
  
  def serialize(self):
    state = {"key": self.key,
             "cards": []}
    for card in self.cards:
      state["cards"].append(card.serialize())
    return state

  def deserialize(self, state):
    for card_state in state["cards"]:
      for card in self.cards:
        if (AccentedText(card.russian.text).text ==
            AccentedText(card_state["russian"]).text and
            AccentedText(card.english.text).text ==
            AccentedText(card_state["english"]).text):
          card.deserialize(card_state)
          break

class CardSetPackage(StudySet):
  def __init__(self, name, path, parent=None):
    # NOTE: Purposefully avoiding super __init__ here
    self.name = name
    self.path = path
    self.parent = parent
    self.card_sets = []
    self.packages = []

  def all_card_sets(self):
    for package in self.packages:
      for card_set in package.all_card_sets():
        yield card_set
    for card_set in self.card_sets:
      yield card_set 

  @property
  def cards(self):
    for card_set in self.all_card_sets():
      for card in card_set.cards:
        yield card

  def serialize(self):
    state = {"card_sets": {}}
    for card_set in self.all_card_sets():
      if card_set.key in state["card_sets"]:
        raise Exception("Duplicate card set key '{}'".format(card_set.key))
      state["card_sets"][card_set.key] = card_set.serialize()
    return state
  
  def deserialize(self, state):
    for card_set in self.all_card_sets():
      if card_set.key in state["card_sets"]:
        card_set.deserialize(state["card_sets"][card_set.key])

  def __getitem__(self, name):
    for package in self.packages:
      if package.name == name:
        return package
    for card_set in self.card_sets:
      if card_set.key == name:
        return card_set
    raise KeyError(name)
