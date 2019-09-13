from study_tool.russian.types import *
from study_tool.russian.word import *

NON_PAST_ORDER = [(Plurality.Singular, Person.First),
                  (Plurality.Singular, Person.Second),
                  (Plurality.Singular, Person.Third),
                  (Plurality.Plural, Person.First),
                  (Plurality.Plural, Person.Second),
                  (Plurality.Plural, Person.Third)]
PAST_ORDER = [(Plurality.Singular, Gender.Masculine),
              (Plurality.Singular, Gender.Femanine),
              (Plurality.Singular, Gender.Neuter),
              (Plurality.Plural, None)]

CONSONANT_MUTATIONS = [
    ("ст", "щ"),
    ("ск", "щ"),
    ("с", "ш"),
    ("х", "ш"),
    ("т", "ч"),
    ("к", "ч"),
    ("д", "ж"),
    ("з", "ж"),
    ("б", "бл"),
    ("п", "пл"),
    ("м", "мл"),
    ("в", "вл"),
    ("ф", "фл")]

LABIAL_CONSONANTS = "бпмвф"


class Verb(Word):
    def __init__(self):
        Word.__init__(self)
        self.word_type = WordType.Verb
        self.infinitive = AccentedText()
        self.translation = AccentedText()
        self.aspect = Aspect.Imperfective
        self.info = AccentedText()
        self.counterparts = []
        self.past = {
            (Plurality.Singular, Gender.Masculine): AccentedText(),
            (Plurality.Singular, Gender.Femanine): AccentedText(),
            (Plurality.Singular, Gender.Neuter): AccentedText(),
            (Plurality.Plural, None): AccentedText()}
        self.non_past = {
            (Plurality.Singular, Person.First): AccentedText(),
            (Plurality.Singular, Person.Second): AccentedText(),
            (Plurality.Singular, Person.Third): AccentedText(),
            (Plurality.Plural, Person.First): AccentedText(),
            (Plurality.Plural, Person.Second): AccentedText(),
            (Plurality.Plural, Person.Third): AccentedText()}
        self.imperative = {
            Plurality.Singular: AccentedText(),
            Plurality.Plural: AccentedText()}
        self.active_participles = {
            Tense.Present: AccentedText(),
            Tense.Past: AccentedText()}
        self.passive_participles = {
            Tense.Present: AccentedText(),
            Tense.Past: AccentedText()}
        self.adverbial_participles = {
            Tense.Present: AccentedText(),
            Tense.Past: AccentedText()}

    def get_info(self) -> AccentedText:
        return self.info

    def get_counterparts(self) -> list:
        return self.counterparts

    def get_translation(self) -> AccentedText:
        return self.translation

    def get_aspect(self) -> Aspect:
        return self.aspect

    def get_all_forms(self):
        return ([self.infinitive] +
                [x for x in self.past.values()] +
                [x for x in self.non_past.values()] +
                [x for x in self.imperative.values()] +
                [x for x in self.active_participles.values()] +
                [x for x in self.passive_participles.values()] +
                [x for x in self.adverbial_participles.values()])

    def remove_reflexive_suffix(self, word) -> AccentedText:
        if word.text.endswith("ся") or word.text.endswith("сь"):
            return AccentedText(word.text[:-2], word.accents)
        else:
            return word

    def get_non_past(self, plurality: Plurality, person: Person) -> AccentedText:
        """Get a non-past conjugation of the verb."""
        return self.non_past[(plurality, person)]

    def get_past(self, plurality=None, gender=None) -> AccentedText:
        """Get a past conjugation of the verb."""
        if plurality is None:
            plurality = Plurality.Singular
        if plurality == Plurality.Plural:
            gender = None
        return self.past[(plurality, gender)]

    def get_non_past_by_index(self, index: int, exclude_reflexive=False) -> AccentedText:
        conjugation = self.non_past[NON_PAST_ORDER[index]]
        if exclude_reflexive:
            conjugation = self.remove_reflexive_suffix(conjugation)
        return conjugation

    def get_past_by_index(self, index, exclude_reflexive=False) -> AccentedText:
        conjugation = self.past[PAST_ORDER[index]]
        if exclude_reflexive:
            conjugation = self.remove_reflexive_suffix(conjugation)
        return conjugation

    def mutate(self, stem):
        for a, b in CONSONANT_MUTATIONS:
            if stem.endswith(a):
                return stem[:-len(a)] + b
        return stem

    def has_form(self, infinitive, non_past=None, past=None, mutate=False) -> bool:
        stem = self.remove_reflexive_suffix(
            self.infinitive).text[:-len(infinitive)]
        if self.remove_reflexive_suffix(self.infinitive).text != stem + infinitive:
            return False
        if past is not None:
            for index, ending in enumerate(past):
                if self.get_past_by_index(index, exclude_reflexive=True).text != stem + ending:
                    return False
        if non_past is not None:
            for index, endings in enumerate(non_past):
                if not isinstance(endings, list) and not isinstance(endings, tuple):
                    endings = [endings]
                matches = False
                for ending in endings:
                    conjugation = self.get_non_past_by_index(
                        index, exclude_reflexive=True).text
                    matches = (conjugation == stem + ending)
                    if not matches and (mutate is True or mutate is index):
                        matches = (conjugation == self.mutate(stem) + ending)
                    if matches:
                        break
                if not matches:
                    return False
        return True

    def classify_conjugation(self) -> VerbSuffix:
        raw_infinitive = self.remove_reflexive_suffix(self.infinitive).text
        if (self.has_form("ать", non_past=["аю", "аешь", "ает", "аем", "аете", "ают"]) or
                self.has_form("ять", non_past=["яю", "яешь", "яет", "яем", "яете", "яют"])):
            return VerbSuffix.Ai
        elif self.has_form("еть", non_past=["ею", "еешь", "еет", "еем", "еете", "еют"]):
            return VerbSuffix.Ei
        elif (self.has_form("овать", non_past=["ую", "уешь", "ует", "уем", "уете", "уют"]) or
              self.has_form("евать", non_past=["ую", "уешь", "ует", "уем", "уете", "уют"]) or
              self.has_form("евать", non_past=["юю", "юешь", "юет", "юем", "юете", "юют"])):
            return VerbSuffix.Ova
        elif (self.has_form("нуть", non_past=["ну", "нешь", "нет", "нем", "нете", "нут"]) or
              self.has_form("нуть", non_past=["ну", "нёшь", "нёт", "нём", "нёте", "нут"])):
            if self.has_form("нуть", past=["нул", "нула", "нуло", "нули"]):
                return VerbSuffix.Nu
            else:
                return VerbSuffix.Nu2
        elif self.has_form("авать", non_past=["аю", "аёшь", "аёт", "аём", "аёте", "ают"]):
            return VerbSuffix.Avai
        elif self.has_form("оть", non_past=["ю", "ешь", "ет", "ем", "ете", "ют"],
                           past=["ол", "ола", "оло", "оли"]):
            return VerbSuffix.O
        elif self.has_form("олоть", non_past=["елю", "елешь", "елет", "елем", "елете", "елют"]):
            return VerbSuffix.O
        elif self.has_form("ать",
                           non_past=["у", "ешь", "ет", "ем", "ете", "ут"],
                           mutate=True):
            return VerbSuffix.A1
        elif (raw_infinitive.endswith("ать") and
              len(raw_infinitive) > 4 and
              raw_infinitive[-4] in (LABIAL_CONSONANTS + "рлн") and
              self.has_form("ать",
                            non_past=["ю", "ешь", "ет", "ем", "ете", "ют"],
                            mutate=True)):
            return VerbSuffix.A1
        elif self.has_form("ять", non_past=["ю", "ешь", "ет", "ем", "ете", "ют"]):
            return VerbSuffix.A2
        elif (self.has_form("ать", non_past=["у", "ёшь", "ёт", "ём", "ёте", "ут"]) or
              self.has_form("рать", non_past=["еру", "ерёшь", "ерёт", "ерём", "ерёте", "ерут"]) or
              self.has_form("вать", non_past=["ову", "овёшь", "овёт", "овём", "овёте", "овут"]) or
              self.has_form("гать", non_past=["гу", "жёшь", "жёт", "жём", "жёте", "гут"])):
            return VerbSuffix.A3
        elif self.has_form("ить",
                           non_past=[("у", "ю"), "ишь", "ит",
                                     "им", "ите", ("ат", "ят")],
                           past=["ил", "ила", "ило", "или"],
                           mutate=0):
            return VerbSuffix.I
        elif (raw_infinitive.endswith("ить") and
              len(raw_infinitive) > 4 and
              raw_infinitive[-4] in (LABIAL_CONSONANTS + "рлн") and
              self.has_form("ить",
                            non_past=["ю", "ишь", "ит",
                                      "им", "ите", ("ат", "ят")],
                            past=["ил", "ила", "ило", "или"],
                            mutate=0)):
            return VerbSuffix.I
        elif self.has_form("еть",
                           non_past=["у", "ишь", "ит", "им", "ите", "ят"],
                           mutate=0):
            return VerbSuffix.E
        elif (raw_infinitive.endswith("еть") and
              len(raw_infinitive) > 4 and
              raw_infinitive[-4] in (LABIAL_CONSONANTS + "рлн") and
              self.has_form("еть",
                            non_past=["ю", "ишь", "ит", "им", "ите", "ят"],
                            mutate=0)):
            return VerbSuffix.E
        elif (self.has_form("ать", non_past=[("у", "ю"), "ишь", "ит", "им", "ите", ("ат", "ят")]) or
              self.has_form("ять", non_past=["ю", "ишь", "ит", "им", "ите", "ят"])):
            return VerbSuffix.Zha
        return None

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
        self.infinitive = self.name
        self.counterparts = []

        self.translation = AccentedText(data["translation"])
        self.info = AccentedText(data.get("info", ""))

        if "infinitive" in data:
            self.infinitive = AccentedText(data["infinitive"])
        if "counterparts" in data:
            self.counterparts = [AccentedText(c) for c in data["counterparts"]]

        if "aspect" in data:
            self.aspect = getattr(Aspect, data["aspect"])
            non_past_list = None
        elif "future" in data:
            self.aspect = Aspect.Perfective
            non_past_list = [AccentedText(x) for x in data["future"]]
        elif "present" in data:
            self.aspect = Aspect.Imperfective
            non_past_list = [AccentedText(x) for x in data["present"]]
        else:
            raise KeyError()

        if non_past_list:
            self.non_past[(Plurality.Singular, Person.First)] = non_past_list[0]
            self.non_past[(Plurality.Singular, Person.Second)] = non_past_list[1]
            self.non_past[(Plurality.Singular, Person.Third)] = non_past_list[2]
            self.non_past[(Plurality.Plural, Person.First)] = non_past_list[3]
            self.non_past[(Plurality.Plural, Person.Second)] = non_past_list[4]
            self.non_past[(Plurality.Plural, Person.Third)] = non_past_list[5]
        else:
            self.non_past[(Plurality.Singular, Person.First)] = AccentedText(
                data["non_past"]["Singular"]["First"])
            self.non_past[(Plurality.Singular, Person.Second)] = AccentedText(
                data["non_past"]["Singular"]["Second"])
            self.non_past[(Plurality.Singular, Person.Third)] = AccentedText(
                data["non_past"]["Singular"]["Third"])
            self.non_past[(Plurality.Plural, Person.First)] = AccentedText(
                data["non_past"]["Plural"]["First"])
            self.non_past[(Plurality.Plural, Person.Second)] = AccentedText(
                data["non_past"]["Plural"]["Second"])
            self.non_past[(Plurality.Plural, Person.Third)] = AccentedText(
                data["non_past"]["Plural"]["Third"])

        if isinstance(data["past"], list):
            self.past[(Plurality.Singular, Gender.Masculine)] = AccentedText(data["past"][0])
            self.past[(Plurality.Singular, Gender.Femanine)] =  AccentedText(data["past"][1])
            self.past[(Plurality.Singular, Gender.Neuter)] =  AccentedText(data["past"][2])
            self.past[(Plurality.Plural, None)] =  AccentedText(data["past"][3])
        else:
            self.past[(Plurality.Singular, Gender.Masculine)] = AccentedText(data["past"]["Masculine"])
            self.past[(Plurality.Singular, Gender.Femanine)] = AccentedText(data["past"]["Femanine"])
            self.past[(Plurality.Singular, Gender.Neuter)] = AccentedText(data["past"]["Neuter"])
            self.past[(Plurality.Plural, None)] = AccentedText(
                data["past"]["Plural"])

        if isinstance(data["imperative"], list):
            self.imperative[Plurality.Singular] = AccentedText(data["imperative"][0])
            self.imperative[Plurality.Plural] = AccentedText(data["imperative"][1])
        else:
            self.imperative[Plurality.Singular] = AccentedText(data["imperative"]["Singular"])
            self.imperative[Plurality.Plural] = AccentedText(data["imperative"]["Plural"])
        
        self.active_participles[Tense.Present] = AccentedText(
            data["participles"]["Active"]["Present"])
        self.active_participles[Tense.Past] = AccentedText(
            data["participles"]["Active"]["Past"])
        self.passive_participles[Tense.Present] = AccentedText(
            data["participles"]["Passive"]["Present"])
        self.passive_participles[Tense.Past] = AccentedText(
            data["participles"]["Passive"]["Past"])
        self.adverbial_participles[Tense.Present] = AccentedText(
            data["participles"]["Adverbial"]["Present"])
        self.adverbial_participles[Tense.Past] = AccentedText(
            data["participles"]["Adverbial"]["Past"])

