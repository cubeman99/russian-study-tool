import os
import random
import re
import time
from study_tool.card import *
from study_tool import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config

TOKEN_DELIMETERS = ["--", "–", "-"]

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
        if (AccentedText(card.russian.text).text ==
            AccentedText(card_state["russian"]).text and
            AccentedText(card.english.text).text ==
            AccentedText(card_state["english"]).text):
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
    raise KeyError(package)

def parse_card_text(text):
  attributes = [CardAttributes(a) for a in re.findall(r"\@(\S+)", text)]
  text = re.sub(r"\@\S+", "", text).strip()
  text = AccentedText(text)
  return text, attributes

def preprocess_lines(filename, lines):
  for line_index, line in enumerate(lines):
    if line.startswith("@googledoc"):
      # Include text from a Google Doc
      tokens = line.strip().split()
      document_id = tokens[1]
      Config.logger.info("Loading googledoc: " + document_id)
      document = googledocs.get_document(document_id)
      title = "googledoc[" + document["title"] + "]"
      for line in preprocess_lines(title, iter(document["text"].splitlines())):
        yield line
    else:
      yield filename, line_index + 1, line

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
      raise Exception("uknown language: '{}'".format(name))

  word_type_dict = {"noun": WordType.Noun,
                    "verb": WordType.Verb,
                    "adjective": WordType.Adjective,
                    "adverb": WordType.Adverb,
                    "none": None}

  with open(path, "r", encoding="utf8") as f:
    filename = path
    line_number = -1
    line = ""
    word_type = None
    card_set = None
    try:
      for filename, line_number, line in preprocess_lines(path, f):
        line = line.strip()
        if line.startswith("@"):
          command = line.split()[0][1:]
          value = line[len(command) + 1:].strip()
          if command == "name":
            card_set = CardSet()
            card_set.name = AccentedText(value)
            card_set.key = card_set.name.text.lower().replace(" ", "_")
            card_sets.append(card_set)
            left_side = CardSide.Russian
          elif command == "key":
            card_set.key = value
          elif command == "info":
            card_set.info = AccentedText(value)
          elif command == "side":
            card_set.side = name_to_side(value)
          elif command == "left":
            left_side = name_to_side(value)
          elif command == "type":
            word_type = word_type_dict[value.lower()]
          else:
            raise Exception("uknown @ command: '{}'".format(command))
        elif line.startswith("#"):
          pass  # ignore comments
        elif len(line) == 0:
          pass  # ignore whitespace
        else:
          tokens = []
          for delimeter in TOKEN_DELIMETERS:
            if delimeter in line:
              tokens = [t.strip() for t in line.split(delimeter)]
              break
          if len(tokens) == 2:
            card = Card()
            card.word_type = word_type
            text, attributes = parse_card_text(tokens[0])
            card.text[left_side] = text
            card.attributes[left_side] = attributes
            text, attributes = parse_card_text(tokens[1])
            card.text[1 - left_side] = text
            card.attributes[1 - left_side] = attributes
            card_set.cards.append(card)
            card_set.card_count = len(card_set.cards)
          else:
            raise Exception("unable to tokenize line")
    except Exception as e:
      Config.logger.error("Exception: {}-{}: {}".format(filename, line_number, line))
      Config.logger.error("{}: {}".format(type(e).__name__, str(e)))
      raise
      exit(1)
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
