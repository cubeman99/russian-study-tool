from study_tool.russian import types
from study_tool.russian.types import Plurality
from study_tool.russian.types import Case
from study_tool.russian.types import Gender
from study_tool.russian.types import WordType
from study_tool.russian.word import AccentedText
from study_tool.russian.word import Word


class NounDeclension:
    def __init__(self):
        self.__declension = {}
        for case in Case:
            for plural in Plurality:
                self.set_declension(case=case, plural=plural, text="")

    def get_declension(self, plural: Plurality, case: Case) -> AccentedText:
        plural = Plurality(plural)
        return self.__declension[(plural, case)]
    
    def set_declension(self, plural: Plurality, case: Case,
                       text: AccentedText):
        plural = Plurality(plural)
        self.__declension[(plural, case)] = AccentedText(text)

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {}
        for case in Case:
            data[types.get_case_short_form_name(case)] = {
                "sing": self.get_declension(case=case, plural=Plurality.Singular).raw,
                "pl": self.get_declension(case=case, plural=Plurality.Plural).raw,
            }
        return data


class Noun(Word):
    def __init__(self):
        Word.__init__(self)
        self.word_type = WordType.Noun
        self.gender = None
        self.indeclinable = False
        self.declension = {
            (Plurality.Singular, Case.Nominative): AccentedText(""),
            (Plurality.Singular, Case.Accusative): AccentedText(""),
            (Plurality.Singular, Case.Genetive): AccentedText(""),
            (Plurality.Singular, Case.Dative): AccentedText(""),
            (Plurality.Singular, Case.Prepositional): AccentedText(""),
            (Plurality.Singular, Case.Instrumental): AccentedText(""),
            (Plurality.Plural, Case.Nominative): AccentedText(""),
            (Plurality.Plural, Case.Accusative): AccentedText(""),
            (Plurality.Plural, Case.Genetive): AccentedText(""),
            (Plurality.Plural, Case.Dative): AccentedText(""),
            (Plurality.Plural, Case.Prepositional): AccentedText(""),
            (Plurality.Plural, Case.Instrumental): AccentedText("")}

    def get_gender(self) -> Gender:
        return self.gender

    def classify_gender(self):
        nom_sing = self.declension[(Plurality.Singular, Case.Nominative)].text
        indeclinable = True
        for case in Case:
            if self.declension[(Plurality.Singular, case)].text != nom_sing:
                indeclinable = False
        if indeclinable:
            return None
        if nom_sing[-1] in "ая":
            return Gender.Femanine
        elif nom_sing[-1] in "оеё":
            return Gender.Neuter
        elif nom_sing[-1] == "ь":
            nom_plur = self.declension[(
                Plurality.Plural, Case.Nominative)].text
            gen_sing = self.declension[(
                Plurality.Singular, Case.Genetive)].text
            if gen_sing[-1] in "ая":
                return Gender.Masculine
            elif gen_sing == nom_plur:
                return Gender.Femanine
        elif nom_sing[-1] == "й" or nom_sing[-1] in CONSONANTS:
            return Gender.Masculine
        return None

    def get_all_forms(self):
        return [x for x in self.declension.values()]
    
    def get_declension(self,
                       plurality=Plurality.Singular,
                       case=Case.Nominative):
        return self.declension[(plurality, case)]
    
    def set_declension(self, plurality: Plurality, case: Case,
                       declension: AccentedText):
        self.declension[(plurality, case)] = AccentedText(declension)

    def serialize(self):
        data = {"declension": {},
                "gender": self.gender.name if self.gender is not None else None,
                "indeclinable": self.indeclinable}
        for plurality in Plurality:
            data["declension"][plurality.name] = {}
            for case in Case:
                data["declension"][plurality.name][case.name] = str(
                    self.declension[(plurality, case)])
        return data

    def deserialize(self, data):
        self.indeclinable = data["indeclinable"]
        self.gender = (getattr(Gender, data["gender"])
                       if data["gender"] is not None else None)
        for plurality in Plurality:
            for case in Case:
                self.declension[(plurality, case)] = AccentedText(
                    data["declension"][plurality.name][case.name])
                
    def __str__(self):
        result = ""
        for case in Case:
            result += case.name.lower() + ":\n"
            for plurality in Plurality:
                form = self.get_declension(case=case, plurality=plurality)
                result += "  " + plurality.name.lower() + ": " + repr(form) + "\n"
        return result[:-1]
