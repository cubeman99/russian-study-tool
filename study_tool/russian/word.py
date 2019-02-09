from study_tool.russian.types import *


ACCENT_CHARS = "'´`\u0301"  # \u0301 is special and rendered on prev char
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


class Verb(Word):
  def __init__(self):
    Word.__init__(self)
    self.word_type = WordType.Verb
    self.infinitive = AccentedText()
    self.translation = AccentedText()
    self.aspect = Aspect.Imperfective
    self.info = AccentedText()
    self.counterparts = []
    self.past = {(Plurality.Singular, Gender.Masculine): "",
                 (Plurality.Singular, Gender.Femanine): "",
                 (Plurality.Singular, Gender.Neuter): "",
                 (Plurality.Plural, None): ""}
    self.non_past = {(Plurality.Singular, Person.First): "",
                     (Plurality.Singular, Person.Second): "",
                     (Plurality.Singular, Person.Third): "",
                     (Plurality.Plural, Person.First): "",
                     (Plurality.Plural, Person.Second): "",
                     (Plurality.Plural, Person.Third): ""}
    self.participles = {}
    self.imperative = {Plurality.Singular: "",
                       Plurality.Plural: ""}
    self.active_participles = {Tense.Present: "",
                               Tense.Past: ""}
    self.passive_participles = {Tense.Present: "",
                                Tense.Past: ""}
    self.adverbial_participles = {Tense.Present: "",
                                 Tense.Past: ""}
    
  def serialize(self):
    data = {
      "infinitive": str(self.infinitive),
      "translation": str(self.translation),
      "info": str(self.info),
      "counterparts": [str(c) for c in self.counterparts],
      "aspect": self.aspect.name,
      "non_past": {
        "Singular": {
          "First": str(self.non_past[(Plurality.Singular, Person.First)]),
          "Second": str(self.non_past[(Plurality.Singular, Person.Second)]),
          "Third": str(self.non_past[(Plurality.Singular, Person.Third)])
          },
        "Plural": {
          "First": str(self.non_past[(Plurality.Plural, Person.First)]),
          "Second": str(self.non_past[(Plurality.Plural, Person.Second)]),
          "Third": str(self.non_past[(Plurality.Plural, Person.Third)])
          }
        },
      "past": {
        "Masculine": str(self.past[(Plurality.Singular, Gender.Masculine)]),
        "Femanine": str(self.past[(Plurality.Singular, Gender.Femanine)]),
        "Neuter": str(self.past[(Plurality.Singular, Gender.Neuter)]),
        "Plural": str(self.past[(Plurality.Plural, None)])
        },
      "imperative": {
        "Singular": str(self.imperative[Plurality.Singular]),
        "Plural": str(self.imperative[Plurality.Plural])
        },
      "participles": {
        "Active": {
          "Present": str(self.active_participles[Tense.Present]),
          "Past": str(self.active_participles[Tense.Past])
          },
        "Passive": {
          "Present": str(self.passive_participles[Tense.Present]),
          "Past": str(self.passive_participles[Tense.Past])
          },
        "Adverbial": {
          "Present": str(self.adverbial_participles[Tense.Present]),
          "Past": str(self.adverbial_participles[Tense.Past])
          }
        }
      }
    return data
  
  def deserialize(self, data):
    self.infinitive = AccentedText(data["infinitive"])
    self.translation = AccentedText(data["translation"])
    self.info = AccentedText(data["info"])
    self.counterparts = [AccentedText(c) for c in data["counterparts"]]
    self.aspect = getattr(Aspect, data["aspect"])
    
    self.non_past[(Plurality.Singular, Person.First)] = AccentedText(data["non_past"]["Singular"]["First"])
    self.non_past[(Plurality.Singular, Person.Second)] = AccentedText(data["non_past"]["Singular"]["Second"])
    self.non_past[(Plurality.Singular, Person.Third)] = AccentedText(data["non_past"]["Singular"]["Third"])
    self.non_past[(Plurality.Plural, Person.First)] = AccentedText(data["non_past"]["Plural"]["First"])
    self.non_past[(Plurality.Plural, Person.Second)] = AccentedText(data["non_past"]["Plural"]["Second"])
    self.non_past[(Plurality.Plural, Person.Third)] = AccentedText(data["non_past"]["Plural"]["Third"])
    self.past[(Plurality.Singular, Gender.Masculine)] = AccentedText(data["past"]["Masculine"])
    self.past[(Plurality.Singular, Gender.Femanine)] = AccentedText(data["past"]["Femanine"])
    self.past[(Plurality.Singular, Gender.Neuter)] = AccentedText(data["past"]["Neuter"])
    self.past[(Plurality.Plural, None)] = AccentedText(data["past"]["Plural"])
    self.imperative[Plurality.Singular] = AccentedText(data["imperative"]["Singular"])
    self.imperative[Plurality.Plural] = AccentedText(data["imperative"]["Plural"])
    self.active_participles[Tense.Present] = AccentedText(data["participles"]["Active"]["Present"])
    self.active_participles[Tense.Past] = AccentedText(data["participles"]["Active"]["Past"])
    self.passive_participles[Tense.Present] = AccentedText(data["participles"]["Passive"]["Present"])
    self.passive_participles[Tense.Past] = AccentedText(data["participles"]["Passive"]["Past"])
    self.adverbial_participles[Tense.Present] = AccentedText(data["participles"]["Adverbial"]["Present"])
    self.adverbial_participles[Tense.Past] = AccentedText(data["participles"]["Adverbial"]["Past"])

