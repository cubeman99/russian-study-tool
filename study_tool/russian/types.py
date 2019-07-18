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
