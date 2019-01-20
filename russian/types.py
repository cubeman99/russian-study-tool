from enum import IntEnum

class Language(IntEnum):
  English = 0
  Russian = 1

class Gender(IntEnum):
  Masculine = 0
  Femanine = 1
  Neuter = 2
  
class Plurality(IntEnum):
  Singular = 0
  Plural = 1
  
class Person(IntEnum):
  First = 0
  Second = 1
  Third = 2

class WordType(IntEnum):
  Noun = 0
  Verb = 1
  Adjective = 2
  Preposition = 3

class Case(IntEnum):
  Nominative = 0
  Accusative = 1
  Genetive = 2
  Dative = 3
  Instrumental = 4
  Prepositional = 5

class Aspect(IntEnum):
  Imperfective = 0
  Perfective = 1

class Tense(IntEnum):
  Present = 0
  Past = 1
  Future = 2
