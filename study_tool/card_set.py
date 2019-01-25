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
    self.age = 0
    self.card_set = None
    self.last_encounter_time = None
    self.marked_count = 0
    self.skipped_count = 0

  @property
  def english(self):
    return self.text[CardSide.English]
  @property
  def russian(self):
    return self.text[CardSide.Russian]
  @property
  def encountered(self):
    return self.last_encounter_time is not None

  def encounter(self):
    self.age = 0

  def mark(self):
    self.marked = True
    self.marked_count += 1
    self.last_encounter_time = time.time()
    
  def skip(self):
    self.marked = False
    self.skipped_count += 1
    self.last_encounter_time = time.time()

  def serialize(self):
    return dict(russian=self.text[CardSide.Russian],
                english=self.text[CardSide.English],
                marked_count=self.marked_count,
                skipped_count=self.skipped_count,
                marked=self.marked,
                last_encounter_time=self.last_encounter_time)

  def deserialize(self, state):
    self.text[CardSide.Russian] = state["russian"]
    self.text[CardSide.English] = state["english"]
    self.marked_count = state["marked_count"]
    self.skipped_count = state["skipped_count"]
    self.marked = state["marked"]
    self.last_encounter_time = state["last_encounter_time"]
  
class CardSet:
  def __init__(self, cards=()):
    self.name = "Untitled"
    self.path = ""
    self.info = ""
    self.cards = list(cards)
    self.card_count = len(cards)
    self.side = CardSide.English

  def next(self, seen, unseen):
    index = random.randint(0, len(unseen) - 1)
    card = unseen[index]
    del unseen[index]
    return card
  
  def serialize(self):
    state = {"name": self.name,
             "cards": []}
    for card in self.cards:
      state["cards"].append(card.serialize())
    return state

  def deserialize(self, state):
    for card_state in state["cards"]:
      for card in self.cards:
        if (card.russian == card_state["russian"] and
            card.english == card_state["english"]):
          card.deserialize(card_state)
          break

class CardSetPackage:
  def __init__(self, name, path, parent=None):
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

  def serialize(self):
    state = {"name": self.name,
             "packages": [],
             "card_sets": []}
    for package in self.packages:
      state["packages"].append(package.serialize())
    for card_set in self.card_sets:
      state["card_sets"].append(card_set.serialize())
    return state
  
  def deserialize(self, state):
    for package_state in state["packages"]:
      for package in self.packages:
        if package.name == package_state["name"]:
          package.deserialize(package_state)
          break
    for card_set_state in state["card_sets"]:
      for card_set in self.card_sets:
        if card_set.name == card_set_state["name"]:
          card_set.deserialize(card_set_state)
          break

def load_card_set_file(path):
  card_set = None
  card_sets = []
  with open(path, "r", encoding="utf8") as f:
    for line in f:
      line = line.strip()
      if line.startswith("@"):
        command = line.split()[0][1:]
        value = line[len(command) + 1:].strip()
        if command == "name":
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

def load_card_package_directory(path, name):
  package = CardSetPackage(name=name, path=path)

  for filename in os.listdir(path):
    file_path = os.path.join(path, filename)
    if os.path.isdir(file_path):
      sub_package = load_card_package_directory(
        path=file_path, name=str(filename))
      if sub_package is not None:
        sub_package.parent = package
        package.packages.append(sub_package)
    elif os.path.isfile(file_path) and file_path.endswith(".txt"):
      package.card_sets += load_card_set_file(file_path)

  if len(package.packages) == 0 and len(package.card_sets) == 0:
    return None
  package.card_sets.sort(key=lambda x: x.name)
  package.packages.sort(key=lambda x: x.name)
  return package
