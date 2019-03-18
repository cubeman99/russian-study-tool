from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian import conjugation

class Adjective(Word):
  def __init__(self):
    Word.__init__(self)
    self.word_type = WordType.Adjective
    self.declension = {}
    self.short_form = {}
    for gender in list(Gender) + [None]:
      self.short_form[gender] = AccentedText("")
      for case in Case:
        self.declension[(gender, case)] = AccentedText("")
  
  def auto_generate_forms(self):
    for gender in list(Gender) + [None]:
      plurality = Plurality.Plural if gender is None else Plurality.Singular
      self.short_form[gender] = conjugation.decline_adjective(
        self.name.text,
        gender=gender,
        plurality=plurality,
        short=True)
      for case in Case:
        self.declension[(gender, case)] = conjugation.decline_adjective(
          self.name.text,
          case=case,
          gender=gender,
          plurality=plurality,
          short=False)

  def get_all_forms(self):
    return ([x for x in self.declension.values()] + 
            [x for x in self.short_form.values()])

  def get_declension(self,
                     gender=Gender.Masculine,
                     plurality=Plurality.Singular,
                     animate=True,
                     case=Case.Nominative,
                     short=False):
    if plurality == Plurality.Plural:
      gender = None
    if short:
      return self.short_form[gender]
    else:
      if case == Case.Accusative and not animate:
        case = Case.Nominative
      return self.declension[(gender, case)]

  def serialize(self):
    data = {"declension": {},
            "short_form": {}}
    for gender in list(Gender) + [None]:
      gender_key = "Plural" if gender is None else gender.name
      data["declension"][gender_key] = {}
      for case in Case:
        data["declension"][gender_key][case.name] = str(
            self.declension[(gender, case)])
      data["short_form"][gender_key] = str(self.short_form[gender])
    return data

  def deserialize(self, data):
    for gender in list(Gender) + [None]:
      gender_key = "Plural" if gender is None else gender.name
      for case in Case:
        self.declension[(gender, case)] = AccentedText(
          data["declension"][gender_key][case.name])
      self.short_form[gender] = AccentedText(data["short_form"][gender_key])
