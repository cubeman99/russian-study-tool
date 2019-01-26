import os
import random
import time
from study_tool.card import *
  
class CardSet:
  def __init__(self, cards=()):
    self.name = "Untitled"
    self.key = None
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
    state = {"key": self.key,
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

  @property
  def cards(self):
    for card_set in self.all_card_sets():
      for card in card_set.cards:
        yield card

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
        if card_set.key == card_set_state["key"]:
          card_set.deserialize(card_set_state)
          break

def load_card_set_file(path):
  card_set = None
  card_sets = []
  left_side = CardSide.Russian

  def name_to_side(name):
    if name.lower() in ["ru", "russian"]:
      return CardSide.Russian
    elif name.lower() in ["en", "english"]:
      return CardSide.English
    else:
      raise KeyError(name)

  with open(path, "r", encoding="utf8") as f:
    for line in f:
      line = line.strip()
      if line.startswith("@"):
        command = line.split()[0][1:]
        value = line[len(command) + 1:].strip()
        if command == "name":
          card_set = CardSet()
          card_set.name = value
          card_set.key = card_set.name.lower().replace(" ", "_")
          card_sets.append(card_set)
          left_side = CardSide.Russian
        elif command == "key":
          card_set.key = value
        elif command == "info":
          card_set.info = value
        elif command == "side":
          card_set.side = name_to_side(value)
        elif command == "left":
          left_side = name_to_side(value)
        else:
          raise KeyError(command)
      elif line.startswith("#"):
        pass  # ignore comments
      else:
        if "-" in line:
          tokens = [t.strip() for t in line.split("-")]
          if len(tokens) == 2:
            card = Card()
            card.text[left_side] = tokens[0]
            card.text[1 - left_side] = tokens[1]
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
