from study_tool.russian.types import *
from study_tool.russian.word import *


class Noun(Word):
    def __init__(self):
        Word.__init__(self)
        self.word_type = WordType.Noun
        self.gender = None
        self.indeclinable = False
        self.declension = {
            (Plurality.Singular, Case.Nominative): "",
            (Plurality.Singular, Case.Accusative): "",
            (Plurality.Singular, Case.Genetive): "",
            (Plurality.Singular, Case.Dative): "",
            (Plurality.Singular, Case.Prepositional): "",
            (Plurality.Singular, Case.Instrumental): "",
            (Plurality.Plural, Case.Nominative): "",
            (Plurality.Plural, Case.Accusative): "",
            (Plurality.Plural, Case.Genetive): "",
            (Plurality.Plural, Case.Dative): "",
            (Plurality.Plural, Case.Prepositional): "",
            (Plurality.Plural, Case.Instrumental): ""}

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
