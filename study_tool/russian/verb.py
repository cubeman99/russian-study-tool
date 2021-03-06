from study_tool.russian import types
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.adjective import Adjective

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


class VerbConjugation:
    """
    Contains verb conjugation information.
    """
    def __init__(self):
        Word.__init__(self)
        self.infinitive = AccentedText()
        self.aspect = Aspect.Imperfective
        self.__past = {
            (Plurality.Singular, Gender.Masculine): AccentedText(),
            (Plurality.Singular, Gender.Femanine): AccentedText(),
            (Plurality.Singular, Gender.Neuter): AccentedText(),
            (Plurality.Plural, None): AccentedText()}
        self.__non_past = {
            (Plurality.Singular, Person.First): AccentedText(),
            (Plurality.Singular, Person.Second): AccentedText(),
            (Plurality.Singular, Person.Third): AccentedText(),
            (Plurality.Plural, Person.First): AccentedText(),
            (Plurality.Plural, Person.Second): AccentedText(),
            (Plurality.Plural, Person.Third): AccentedText()}
        self.__imperative = {
            Plurality.Singular: AccentedText(),
            Plurality.Plural: AccentedText()}
        self.__participles = {}
        for participle in (Participle.Active, Participle.Passive, Participle.Adverbial):
            for tense in (Tense.Past, Tense.Present):
                self.__participles[(participle, tense)] = AccentedText()

    def get_aspect(self) -> Aspect:
        return self.aspect

    def get_non_past(self, plural: Plurality, person: Person) -> AccentedText:
        """Get a non-past conjugation of the verb."""
        return self.__non_past[(Plurality(plural), person)]

    def get_past(self, plural=None, gender=None) -> AccentedText:
        """Get a past conjugation of the verb."""
        if plural is None:
            plural = plural.Singular
        else:
            plural = Plurality(plural)
        if plural == plural.Plural:
            gender = None
        return self.__past[(plural, gender)]

    def get_imperative(self, plural: Plurality):
        """Gets a imperative form of the verb."""
        return self.__imperative[Plurality(plural)]

    def get_participle(self, participle: Participle, tense: Tense) -> AccentedText:
        """Gets a participle form of the verb."""
        return self.__participles[(participle, tense)]

    def set_non_past(self, plural: Plurality, person: Person, text: AccentedText):
        """Sets a non-past conjugation of the verb."""
        self.__non_past[(Plurality(plural), person)] = AccentedText(text)

    def set_past(self, plural: Plurality, gender: Gender, text: AccentedText):
        """Sets a past conjugation of the verb."""
        if plural is None:
            plural = Plurality.Singular
        else:
            plural = Plurality(plural)
        if plural == Plurality.Plural:
            gender = None
        self.__past[(plural, gender)] = AccentedText(text)

    def set_participle(self, participle: Participle, tense: Tense, text: AccentedText):
        """Sets a participle of the verb."""
        self.__participles[(participle, tense)] = AccentedText(text)

    def set_imperative(self, plural: Plurality, text: AccentedText):
        """Sets a imperative form of the verb."""
        self.__imperative[Plurality(plural)] = AccentedText(text)

    def serialize(self):
        """Serialize the state of this object into a dictionary."""
        data = {
            "infinitive": self.infinitive.raw,
            "aspect": types.get_aspect_short_form_name(self.aspect),
            "non_past": {
                "sing": {
                    "1st": self.get_non_past(plural=Plurality.Singular, person=Person.First).raw,
                    "2nd": self.get_non_past(plural=Plurality.Singular, person=Person.Second).raw,
                    "3rd": self.get_non_past(plural=Plurality.Singular, person=Person.Third).raw,
                },
                "pl": {
                    "1st": self.get_non_past(plural=Plurality.Plural, person=Person.First).raw,
                    "2nd": self.get_non_past(plural=Plurality.Plural, person=Person.Second).raw,
                    "3rd": self.get_non_past(plural=Plurality.Plural, person=Person.Third).raw,
                }
            },
            "past": {
                "m": self.get_past(plural=Plurality.Singular, gender=Gender.Masculine).raw,
                "n": self.get_past(plural=Plurality.Singular, gender=Gender.Neuter).raw,
                "f": self.get_past(plural=Plurality.Singular, gender=Gender.Femanine).raw,
                "pl": self.get_past(plural=Plurality.Plural, gender=None).raw,
            },
            "imperative": {
                "sing": self.get_imperative(Plurality.Singular).raw,
                "pl": self.get_imperative(Plurality.Plural).raw,
            }
        }

        # Serialize participles
        data["participles"] = {}
        for participle in Participle:
            participle_key = participle.name.lower()
            data["participles"][participle_key] = {}
            for tense in (Tense.Past, Tense.Present):
                tense_key = tense.name.lower()
                form = self.get_participle(participle=participle, tense=tense)
                data["participles"][participle_key][tense_key] = form.raw

        return data



class Verb(Word):
    def __init__(self):
        Word.__init__(self)
        self.word_type = WordType.Verb
        self.infinitive = AccentedText()
        self.translation = AccentedText()
        self.aspect = Aspect.Imperfective
        self.info = AccentedText()
        self.reflexive = False
        self.transitive = False
        self.conjugation_class = None
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

        self.__participles = {}
        self.__participle_words = {}
        for participle in (Participle.Active, Participle.Passive, Participle.Adverbial):
            for tense in (Tense.Past, Tense.Present):
                self.__participles[(participle, tense)] = AccentedText()
                if participle in (Participle.Active, Participle.Passive):
                    self.__participle_words[(participle, tense)] = None

    def get_info(self) -> AccentedText:
        return self.info

    def get_counterparts(self) -> list:
        return self.counterparts

    def get_translation(self) -> AccentedText:
        return self.translation

    def get_aspect(self) -> Aspect:
        return self.aspect

    def get_all_forms(self):
        forms = ([self.infinitive] +
                [x for x in self.past.values()] +
                [x for x in self.non_past.values()] +
                [x for x in self.imperative.values()])
        for _, adjective in self.__participle_words.items():
             forms += adjective.get_all_forms()
        return forms

    def remove_reflexive_suffix(self, word) -> AccentedText:
        if word.text.endswith("ся") or word.text.endswith("сь"):
            return AccentedText(word.text[:-2], word.accents)
        else:
            return word

    def get_participles_words(self) -> list:
        return list(self.__participle_words.values())

    def get_participle(self, participle: Participle, tense: Tense) -> AccentedText:
        """Get a participle of the verb."""
        return self.__participles[(participle, tense)]

    def get_participle_word(self, participle: Participle, tense: Tense) -> Adjective:
        """Get a participle of the verb."""
        return self.__participle_words[(participle, tense)]

    def set_participle(self, participle: Participle, tense: Tense, text: AccentedText):
        """Sets a participle of the verb."""
        self.__participles[(participle, tense)] = AccentedText(text)
        adjective = Adjective(text)
        adjective.auto_generate_forms()
        if participle in (Participle.Active, Participle.Passive):
            self.__participle_words[(participle, tense)] = adjective

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

    def set_non_past(self, plurality: Plurality, person: Person, text: AccentedText):
        """Sets a non-past conjugation of the verb."""
        self.non_past[(plurality, person)] = AccentedText(text)

    def set_past(self, plurality: Plurality, gender: Gender, text: AccentedText):
        """Sets a past conjugation of the verb."""
        if plurality is None:
            plurality = Plurality.Singular
        if plurality == Plurality.Plural:
            gender = None
        self.past[(plurality, gender)] = AccentedText(text)

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
            }
        }

        # Serialize participles
        data["participles"] = {}
        for participle in Participle:
            participle_key = participle.name
            data["participles"][participle_key] = {}
            for tense in (Tense.Past, Tense.Present):
                tense_key = tense.name
                data["participles"][participle_key][tense_key] = str(
                    self.get_participle(participle=participle, tense=tense))

        return data

    def deserialize(self, data):
        self.infinitive = self.name
        self.counterparts = []

        self.translation = AccentedText(data["translation"])
        self.info = AccentedText(data.get("info", ""))

        if "infinitive" in data:
            self.infinitive = AccentedText(data["infinitive"])
        if "counterparts" in data:
            self.counterparts = [AccentedText(c) for c in data["counterparts"] if c]

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
        
        # Deserialize participles
        for participle in Participle:
            participle_key = participle.name
            for tense in (Tense.Past, Tense.Present):
                tense_key = tense.name
                text = data["participles"][participle_key][tense_key]
                self.set_participle(participle=participle, tense=tense, text=text)

    def __str__(self):
        import yaml
        data = self.serialize()
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)[:-1]
        result = ""
        for case in Case:
            result += case.name.lower() + ":\n"
            for plurality in Plurality:
                form = self.get_declension(case=case, plurality=plurality)
                result += "  " + plurality.name.lower() + ": " + repr(form) + "\n"
        return result[:-1]
