from study_tool.russian.types import *
from study_tool.russian import types
from study_tool.russian.word import *
from study_tool.russian import conjugation


class AdjectiveDeclension:
    def __init__(self):
        self.case_forms = {}
        self.short_form = {}
        for gender in list(Gender) + [None]:
            self.set_short_form(gender=gender, text="")
            for case in Case:
                self.set_case_form(case=case, gender=gender, text="")

    def set_short_form(self, gender: Gender, text: AccentedText):
        self.short_form[gender] = AccentedText(text)

    def set_case_form(self, case: Case, gender: Gender, text: AccentedText):
        self.short_form[(case, gender)] = AccentedText(text)

    def get_short_form(self, gender: Gender):
        return self.short_form[gender]

    def get_case_form(self, case: Case, gender: Gender):
        return self.short_form[(case, gender)]
            
    def set_declension(self,
                       text: AccentedText,
                       gender=Gender.Masculine,
                       plurality=Plurality.Singular,
                       case=Case.Nominative,
                       short=False):
        """
        Sets a declension of the adjective.
        Assumes animate for genitive.
        """
        if plurality == Plurality.Plural:
            gender = None
        if short:
            self.set_short_form(gender=gender, text=text)
        else:
            self.set_case_form(case=case, gender=gender, text=text)
            
    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {}
        for case in Case:
            data[types.get_case_short_form_name(case)] = {
                "m": self.get_case_form(case=case, gender=Gender.Masculine).raw,
                "n": self.get_case_form(case=case, gender=Gender.Neuter).raw,
                "f": self.get_case_form(case=case, gender=Gender.Femanine).raw,
                "pl": self.get_case_form(case=case, gender=None).raw,
            }
        data["short"] =  {
            "m": self.get_short_form(gender=Gender.Masculine).raw,
            "n": self.get_short_form(gender=Gender.Neuter).raw,
            "f": self.get_short_form(gender=Gender.Femanine).raw,
            "pl": self.get_short_form(gender=None).raw
        }
        return data
    

class Adjective(Word):
    def __init__(self, name=None):
        Word.__init__(self, name=name)
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
        """Get a declension of the adjective."""
        if plurality == Plurality.Plural:
            gender = None
        if short:
            return self.short_form[gender]
        else:
            if (case == Case.Accusative and not animate and
                    gender != Gender.Femanine):
                case = Case.Nominative
            return self.declension[(gender, case)]

    def set_declension(self,
                       text: AccentedText,
                       gender=Gender.Masculine,
                       plurality=Plurality.Singular,
                       case=Case.Nominative,
                       short=False):
        """
        Sets a declension of the adjective.
        Assumes animate for genitive.
        """
        if plurality == Plurality.Plural:
            gender = None
        if short:
            self.short_form[gender] = AccentedText(text)
        else:
            self.declension[(gender, case)] = AccentedText(text)

    def has_short_form(self) -> bool:
        """Returns True if the adjective has a short form."""
        return has_russian_letters(self.short_form[Gender.Masculine])

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
            self.short_form[gender] = AccentedText(
                data["short_form"][gender_key])
