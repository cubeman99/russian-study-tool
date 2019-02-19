import os
import random
import re
import time
from study_tool.card import Card, CardSide, SourceLocation
from study_tool.card_set import CardSet, CardSetPackage
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config


TOKEN_DELIMETERS = ["--", "–", "-"]
WORD_TYPE_DICT = {"noun": WordType.Noun,
                  "verb": WordType.Verb,
                  "adjective": WordType.Adjective,
                  "adverb": WordType.Adverb,
                  "preposition": WordType.Preposition,
                  "conjunction": WordType.Conjunction,
                  "pronoun": WordType.Pronoun,
                  "none": None,
                  None: None}

class CardDatabase():
  def __init__(self):
    self.cards = {}

  def add_card(self, card: Card):
    key = card.get_key()
    if key in self.cards:
      raise Exception("Duplicate card: " + repr(key))
    self.cards[key] = card
  
  def serialize_study_data(self):
    state = {"save_time": time.time(),
             "cards": []}
    for _, card in self.cards.items():
      card_state = card.serialize()
      card_state["type"] = None if card.word_type is None else card.word_type.name
      card_state["russian"] = card.russian.text
      card_state["english"] = card.english.text
      state["cards"].append(card_state)
    return state

  def deserialize_study_data(self, state):
    for card_state in state["cards"]:
      word_type = card_state["type"]
      if word_type is not None:
        word_type = getattr(WordType, word_type)
      key = (word_type,
             AccentedText(card_state["russian"]).text,
             AccentedText(card_state["english"]).text)
      if key in self.cards:
        card = self.cards[key]
        card.deserialize(card_state)
      else:
        Config.logger.warning("Card not found: " + repr(key))

  def parse_card_text(self, text, split=False):
    attributes = []
    for name in re.findall(r"\@(\S+)", text):
      attribute = CardAttributes(name)
      try:
        attributes.append(attribute)
      except:
        raise Exception("unknown card attribute '{}'".format(name))
    text = re.sub(r"\@\S+", "", text).strip()
    if split:
      text = [AccentedText(x.strip()) for x in text.split("/")]
    else:
      text = AccentedText(text)
    return text, attributes

  def preprocess_lines(self, filename, lines):
    for line_index, line in enumerate(lines):
      if line.startswith("@googledoc"):
        # Include text from a Google Doc
        tokens = line.strip().split()
        document_id = tokens[1]
        Config.logger.info("Loading googledoc: " + document_id)
        document = googledocs.get_document(document_id)
        title = "googledoc[" + document["title"] + "]"
        for line in self.preprocess_lines(title, iter(document["text"].splitlines())):
          yield line
      else:
        yield filename, line_index + 1, line


  def load_card_set_file(self, path):
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

    with open(path, "r", encoding="utf8") as f:
      filename = path
      line_number = -1
      line = ""
      word_type = None
      card_set = None
      split_attributes = None
      try:
        for filename, line_number, line in self.preprocess_lines(path, f):
          line = line.strip()
          if line.startswith("@"):
            command = line.split()[0][1:]
            value = line[len(command) + 1:].strip()
            if command == "name":
              card_set = CardSet()
              card_set.source = SourceLocation(filename=filename,
                                               line_number=line_number,
                                               line_text=line)
              card_set.name = AccentedText(value)
              card_set.key = card_set.name.text.lower().replace(" ", "_")
              card_sets.append(card_set)
              left_side = CardSide.Russian
              split_attributes = None
            elif command == "key":
              card_set.key = value
            elif command == "info":
              card_set.info = AccentedText(value)
            elif command == "side":
              card_set.side = name_to_side(value)
            elif command == "left":
              left_side = name_to_side(value)
            elif command == "split":
              split_sides = [v.strip() for v in value.split("/")]
              split_attributes = []
              for attr_list in split_sides:
                split_attributes.append([CardAttributes(x.strip())
                                         for x in attr_list.split()])
            elif command == "type":
              word_type = WORD_TYPE_DICT[value.lower()]
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
              text_l_list, attributes_l = self.parse_card_text(tokens[0], split=True)
              text_r, attributes_r = self.parse_card_text(tokens[1])
              if len(text_l_list) > 1:
                if split_attributes is None:
                  raise Exception("detected '/' with no split configured")
                if len(split_attributes) != len(text_l_list):
                  raise Exception("mismatch with split size of {}"
                                  .format(len(split_attributes)))
              for split_index, text_l in enumerate(text_l_list):
                card = Card()
                card.source = SourceLocation(filename=filename,
                                             line_number=line_number,
                                             line_text=line)
                card.word_type = word_type
                card.text[left_side] = text_l
                card.text[1 - left_side] = text_r
                card.add_attributes(attributes_l, left_side)
                card.add_attributes(attributes_r, 1 - left_side)
                if split_attributes is not None and len(text_l_list) > 1:
                  card.add_attributes(attrs=split_attributes[split_index],
                                      side=1 - left_side)
                card_set.cards.append(card)
                self.add_card(card)
            else:
              raise Exception("unable to tokenize line")
      except Exception as e:
        Config.logger.error("Exception: {}-{}: {}".format(filename, line_number, line))
        Config.logger.error("{}: {}".format(type(e).__name__, str(e)))
        raise
        exit(1)
    return sorted(card_sets, key=lambda x: x.name)

  def load_card_package_directory(self, path, name) -> CardSetPackage:
    package = CardSetPackage(name=name, path=path)

    for filename in os.listdir(path):
      file_path = os.path.join(path, filename)
      if os.path.isdir(file_path):
        sub_package = self.load_card_package_directory(
          path=file_path, name=str(filename))
        if sub_package is not None:
          sub_package.parent = package
          package.packages.append(sub_package)
      elif os.path.isfile(file_path) and file_path.endswith(".txt"):
        package.card_sets += self.load_card_set_file(file_path)

    if len(package.packages) == 0 and len(package.card_sets) == 0:
      return None
    package.card_sets.sort(key=lambda x: x.name)
    package.packages.sort(key=lambda x: x.name)
    return package

