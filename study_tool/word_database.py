import json
import shutil
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.card import *
from study_tool.card_attributes import *
from study_tool.config import Config


class WordDatabase:
  def __init__(self):
    self.words = {}

  def get_word(self, name, word_type):
    key = name.text
    if key in self.words:
      word = self.words[key]
    elif word_type == WordType.Verb:
      word = self.add_verb(name)
      self.words[key] = word
    elif word_type == WordType.Noun:
      word = self.add_noun(name)
      self.words[key] = word
    elif word_type == WordType.Adjective:
      word = self.add_adjective(name)
      self.words[key] = word
    else:
      return None
    if word is not None and word.word_type != word_type:
      raise Exception(word.word_type)
    return word

  def __getitem__(self, name):
    name = AccentedText(name).text
    return self.words[name]

  def populate_card_details(self, card) -> bool:
    if card.word is None and card.word_type is not None:
      word = self.get_word(name=card.russian,
                           word_type=card.word_type)
      if word is not None:
        card.word = word
        if isinstance(word, Verb):
          if word.aspect == Aspect.Imperfective:
            card.add_attribute(CardAttributes.Imperfective, side=CardSide.English)
          elif word.aspect == Aspect.Perfective:
            card.add_attribute(CardAttributes.Perfective, side=CardSide.English)
          suffix = word.classify_conjugation()
          if suffix is not None:
            card.add_attribute(VERB_SUFFIX_TO_ATTRIBUTE[suffix], side=CardSide.English)
        elif isinstance(word, Noun):
          if CardAttributes.Indeclinable in card.attributes[CardSide.Russian]:
            word.gender = None
          else:
            for gender, attr in GENDER_TO_ATTRIBUTE.items():
              if attr in card.attributes[CardSide.Russian]:
                word.gender = gender
            if word.gender is not None:
              card.add_attribute(GENDER_TO_ATTRIBUTE[word.gender],
                                 side=CardSide.Russian)
          if word.gender is None:
            word.indeclinable = True
            card.add_attribute(CardAttributes.Indeclinable,
                                side=CardSide.Russian)
        return True
    return False

  def add_verb(self, infinitive):
    from study_tool.external import cooljugator
    Config.logger.info("Downloading verb info for " + infinitive)
    verb = cooljugator.get_verb_info(infinitive)
    if verb is not None:
      self.add_word(verb)
    return verb

  def add_noun(self, dictionary_form):
    from study_tool.external import cooljugator
    Config.logger.info("Downloading noun info for " + dictionary_form)
    noun = cooljugator.get_noun_info(dictionary_form)
    if noun is not None:
      self.add_word(noun)
    return noun

  def add_adjective(self, dictionary_form):
    from study_tool.external import cooljugator
    Config.logger.info("Downloading adjective info for " + dictionary_form)
    adjective = cooljugator.get_adjective_info(dictionary_form)
    if adjective is not None:
      self.add_word(adjective)
    return adjective

  def add_word(self, word):
    key = word.name.text
    if key in self.words:
      raise Exception("Duplicate word: " + word.name.text)
    self.words[key] = word
    return word

  def save(self, path):
    word_data = self.serialize()
    temp_path = path + ".temp"
    with open(temp_path, "w", encoding="utf8") as f:
      json.dump(word_data, f, indent=2, sort_keys=True, ensure_ascii=False)
    shutil.move(temp_path, path)

  def load(self, path):
    with open(path, "r", encoding="utf8") as f:
      word_data = json.load(f)
    self.deserialize(word_data)

  def serialize(self):
    data = {"words": []}
    for name, word in self.words.items():
      if word is not None:
        word_data = Word.serialize(word)
        data["words"].append(word_data)
    return data

  def deserialize(self, data):
    self.words = {}
    for word_data in data["words"]:
      word_type = getattr(WordType, word_data["type"])
      word = None
      if word_type == WordType.Verb:
        word = Verb()
      elif word_type == WordType.Adjective:
        word = Adjective()
      elif word_type == WordType.Noun:
        word = Noun()
      Word.deserialize(word, word_data)
      word.deserialize(word_data[word_type.name])
      self.add_word(word)
