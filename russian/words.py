from russian.types import *

class Word(Card):
  def __init__(self, english, russian,
               word_type=WordType.Noun,
               case=Case.Nominative,
               plurality=Plurality.Singular,
               gender=None,
               person=None,
               tense=None,
               aspect=None):
    self.english = english
    self.russian = russian
    self.word_type = word_type
    self.gender = gender
    self.case = case
    self.plurality = plurality
    self.person = person
    self.aspect = aspect
    self.tense = tense
