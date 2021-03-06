from enum import IntEnum


class WordType(IntEnum):
    Noun = 0
    Verb = 1
    Adjective = 2
    Preposition = 3
    Adverb = 4
    Conjunction = 5
    Pronoun = 7
    Other = 8
    Phrase = 9
    Interjection = 10
    Particle = 11
    Numeral = 12


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
    

class Participle(IntEnum):
    Active = 0
    Passive = 1
    Adverbial = 2


class Person(IntEnum):
    First = 0
    Second = 1
    Third = 2


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


class Animacy(IntEnum):
    Animate = 0
    Inanimate = 1


class VerbSuffix(IntEnum):
    Ai = 0
    Ei = 1
    Ova = 2
    Nu = 3
    Nu2 = 4
    A1 = 5
    A2 = 5
    A3 = 5
    Avai = 6
    O = 7
    I = 8
    E = 9
    Zha = 10
    Resonant = 11
    Obstruent = 12

   
__WORD_TYPE_TO_SHORT_NAME_DICT = {
    WordType.Noun: "n",
    WordType.Verb: "v",
    WordType.Adjective: "adj",
    WordType.Adverb: "adv",
    WordType.Preposition: "prep",
    WordType.Conjunction: "cj",
    WordType.Pronoun: "pro",
    WordType.Phrase: "ph",
    WordType.Other: "oth",
    WordType.Interjection: "int",
    WordType.Particle: "part",
    WordType.Numeral: "num",
}

__CASE_SHORT_NAMES = {
    Case.Nominative: "nom",
    Case.Accusative: "acc",
    Case.Genetive: "gen",
    Case.Dative: "dat",
    Case.Instrumental: "instr",
    Case.Prepositional: "prep",
}

__ASPECT_SHORT_NAMES = {
    Aspect.Perfective: "pf",
    Aspect.Imperfective: "impf",
}

__SHORT_NAME_TO_WORD_TYPE_DICT = dict(
    (v, k) for k, v in __WORD_TYPE_TO_SHORT_NAME_DICT.items())

__STRING_TO_WORD_TYPE_DICT = {"none": WordType.Other,
                  None: WordType.Other}
for word_type in WordType:
    __STRING_TO_WORD_TYPE_DICT[word_type.name.lower()] = word_type

def get_word_type_short_name(word_type: WordType) -> str:
    return __WORD_TYPE_TO_SHORT_NAME_DICT[word_type]

def get_case_short_form_name(case: Case) -> str:
    return __CASE_SHORT_NAMES[case]

def get_aspect_short_form_name(case: Case) -> str:
    return __ASPECT_SHORT_NAMES[case]

def parse_word_type(text, strict=False) -> WordType:
    if strict:
       return __STRING_TO_WORD_TYPE_DICT[text.lower()]
    else:
        return __STRING_TO_WORD_TYPE_DICT.get(text.lower(), WordType.Other)

def parse_short_word_type(text) -> WordType:
    return __SHORT_NAME_TO_WORD_TYPE_DICT.get(text.lower(), None)

def parse_aspect(text: str) -> Aspect:
    text = text.lower()
    if text in ["imperfective", "impf"]:
        return Aspect.Imperfective
    if text in ["perfective", "pf"]:
        return Aspect.Perfective
    raise ValueError(text)

def parse_case(text: str) -> Case:
    text = text.lower()
    if text in ["nominative", "nom"]:
        return Case.Nominative
    if text in ["accusative", "acc"]:
        return Case.Accusative
    if text in ["genetive", "genitive", "gen"]:
        return Case.Genetive
    if text in ["dative", "dat"]:
        return Case.Dative
    if text in ["instrumental", "instr"]:
        return Case.Instrumental
    if text in ["prepositional", "prep"]:
        return Case.Prepositional
    raise ValueError(text)
