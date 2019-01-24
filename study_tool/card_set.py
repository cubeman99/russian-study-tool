from enum import IntEnum
import os
import pygame
import random
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *

class CardSide(IntEnum):
  Russian = 0
  English = 1

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
    self.info = ""
    self.cards = list(cards)
    self.card_count = len(cards)
    self.side = CardSide.Russian

  def next(self):
    index = random.randint(0, len(self.cards) - 1)
    card = self.cards[index]
    del self.cards[index]
    return card

def load_card_set_file(path):
  print("Loading card set file: " + path)
  card_set = None
  card_sets = []
  with open(path, "r", encoding="utf8") as f:
    for line in f:
      line = line.strip()
      if line.startswith("@"):
        command = line.split()[0][1:]
        value = line[len(command) + 1:].strip()
        if command == "name":
          print(" - New card set: " + value)
          card_set = CardSet()
          card_set.name = value
          card_sets.append(card_set)
        elif command == "info":
          card_set.info = value
        elif command == "side":
          card_set.side = CardSide.Russian if value in ["ru", "russian"] else CardSide.English
        else:
          raise KeyError(command)
      elif line.startswith("#"):
        pass  # ignore comments
      else:
        if "-" in line:
          tokens = [t.strip() for t in line.split("-")]
          if len(tokens) == 2:
            card = Card(tokens[0], tokens[1])
            card_set.cards.append(card)
            card_set.card_count = len(card_set.cards)
  return sorted(card_sets, key=lambda x: x.name)
