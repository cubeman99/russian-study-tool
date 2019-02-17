from study_tool.russian.types import *

CONSONANTS = "бвгджзклмнпрстфхцчшщй"
VOWELS = "аэыуояеёюи"
ACCENT_CHAR = "´"
ACCENT_CHARS = "'´`"
HARD_VOWELS = "аоуыэ"
SOFT_VOWELS = "яёюие"
TO_SOFT = {"а": "я",
           "о": "ё",
           "у": "ю",
           "ы": "и",
           "э": "е"}

ACCENT_CHARS = "'’´`\u0301"  # \u0301 is special and rendered on prev char
STANDARD_ACCENT_CHAR = "'"


def get_word_text(word):
  word = word.lower()
  for c in ACCENT_CHARS:
    word = word.replace(c, "")
  return word


def get_stress_index(word):
  word = word.lower().strip()
  stress = None
  for c in ACCENT_CHARS:
    if c in word:
      stress = word.index(c) - 1
      break
  return stress

class AccentedText:
  def __init__(self, text="", accents=None):
    if isinstance(text, AccentedText):
      self.text = text.text
      self.accents = tuple(text.accents)
    else:
      text = text
      length = 0
      if accents is None:
        self.accents = ()
        self.text = ""
        for index, c in enumerate(text):
          x = ord(c)
          if c in ACCENT_CHARS:
            if length > 0:
              self.accents += (length - 1,)
          else:
            self.text += c
            length += 1
      else:
        self.text = text
        self.accents = tuple(accents)

  def __getitem__(self, index):
    return (self.text[index], index in self.accents)
    
  def __lt__(self, other):
    if isinstance(other, AccentedText):
      return self.text < other.text
    else:
      return self.text < str(other)

  def __add__(self, other):
    if isinstance(other, AccentedText):
      return AccentedText(
        self.text + other.text,
        self.accents + tuple(a + len(self.text) for a in other.accents))
    else:
      return AccentedText(
        self.text + str(other),
        self.accents)
  
  def __radd__(self, other):
    if isinstance(other, AccentedText):
      raise Exception(other)
    else:
      return AccentedText(
        str(other) + self.text,
        tuple(a + len(other) for a in self.accents))
  
  def __str__(self):
    return repr(self)

  def __repr__(self):
    result = ""
    for c, accented in self:
      result += c
      if accented:
        result += STANDARD_ACCENT_CHAR
    return result


class Word:
  def __init__(self):
    self.word_type = WordType.Noun
    self.name = AccentedText()
    self.examples = []

  def serialize(self):
    data = {"type": self.word_type.name,
            "name": str(self.name),
            "examples": []}
    for russian, english in self.examples:
      data["examples"].append({
        "Russian": str(russian),
        "English": str(english)
        })
    data[self.word_type.name] = self.serialize()
    return data
  
  def deserialize(self, data):
    self.name = AccentedText(data["name"])
    self.word_type = getattr(WordType, data["type"])
    self.examples = []
    for example in data["examples"]:
      self.examples.append((AccentedText(example["Russian"]),
                            AccentedText(example["English"])))
