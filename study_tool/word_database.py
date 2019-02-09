from study_tool.russian.types import *
from study_tool.russian.word import *
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
    else:
      raise Exception(word_type)
    if word.word_type != word_type:
      raise Exception(word.word_type)
    return word

  def add_verb(self, infinitive):
    from study_tool import conjugator
    Config.logger.info("Downloading verb info for " + infinitive)
    verb = conjugator.get_verb_info(infinitive)
    if verb is None:
      raise Exception(verb)
    self.add_word(verb)
    return verb

  def add_word(self, word):
    key = word.name.text
    if key in self.words:
      raise Exception("Duplicate word: " + word.name)
    self.words[key] = word
    return word

  def serialize(self):
    data = {"words": []}
    for name, word in self.words.items():
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
