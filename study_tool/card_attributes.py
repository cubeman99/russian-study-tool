from enum import Enum, IntEnum
import os
import time
from study_tool.config import Config
from study_tool.russian.word import *
from cmg.color import Color


class CardAttributes(Enum):
    Masculine = "m"
    Femanine = "f"
    Neuter = "n"
    Singular = "sing"
    Plural = "pl"
    NoPural = "nopl"
    PluralOnly = "pluronly"
    SingularOnly = "singonly"
    FirstPerson = "1st"
    SecondPerson = "2nd"
    ThirdPerson = "3rd"
    Perfective = "pf"
    Imperfective = "impf"
    Informal = "informal"
    Formal = "formal"
    Unidirectional = "uni"
    Multidirectional = "multi"
    Nominative = "nom"
    Accusative = "acc"
    Genetive = "gen"
    Dative = "dat"
    Prepositional = "prep"
    Instrumental = "instr"
    Indeclinable = "indec"
    Irregular = "irreg"
    Animate = "anim"
    Inanimate = "inanim"
    Transative = "trans"
    Intransative = "intrans"
    Reflexive = "reflex"
    Short = "short"
    Long = "long"
    Infinitive = "infinitive"
    VerbSuffixAi = "verb.suffix.ai"
    VerbSuffixEi = "verb.suffix.ei"
    VerbSuffixOva = "verb.suffix.ova"
    VerbSuffixNu = "verb.suffix.nu"
    VerbSuffixNu2 = "verb.suffix.nu2"
    VerbSuffixA1 = "verb.suffix.a1"
    VerbSuffixA2 = "verb.suffix.a2"
    VerbSuffixA3 = "verb.suffix.a3"
    VerbSuffixAvai = "verb.suffix.avai"
    VerbSuffixO = "verb.suffix.o"
    VerbSuffixI = "verb.suffix.i"
    VerbSuffixE = "verb.suffix.e"
    VerbSuffixZha = "verb.suffix.zha"
    ResonantStem = "stem.resonant"
    ObstruentStem = "stem.obstruent"
    Past = "past"
    NonPast = "nonpast"
    AdjectiveAsNoun = "adjasnoun"
    VerbOfMotion = "verb_of_motion"
    Curse = "curse"


# Attributes that must be shown in order to translate from english to russian
ENGLISH_SIDE_CARD_ATTRIBUTES = [
    # For word choice
    CardAttributes.Perfective,
    CardAttributes.Imperfective,
    CardAttributes.Unidirectional,
    CardAttributes.Multidirectional,

    # For word conjugations
    CardAttributes.Short,
    CardAttributes.Long,
    CardAttributes.Infinitive,
    CardAttributes.Past,
    CardAttributes.NonPast,
    CardAttributes.FirstPerson,
    CardAttributes.SecondPerson,
    CardAttributes.ThirdPerson,
    CardAttributes.Animate,
    CardAttributes.Inanimate,
    CardAttributes.Formal,
    CardAttributes.Informal,
]

CASE_TO_ATTRIBUTE = {
    Case.Nominative: CardAttributes.Nominative,
    Case.Accusative: CardAttributes.Accusative,
    Case.Genetive: CardAttributes.Genetive,
    Case.Prepositional: CardAttributes.Prepositional,
    Case.Dative: CardAttributes.Dative,
    Case.Instrumental: CardAttributes.Instrumental}

PLURALITY_TO_ATTRIBUTE = {
    Plurality.Singular: CardAttributes.Singular,
    Plurality.Plural: CardAttributes.Plural}

ASPECT_TO_ATTRIBUTE = {
    Aspect.Imperfective: CardAttributes.Imperfective,
    Aspect.Perfective: CardAttributes.Perfective}

PERSON_TO_ATTRIBUTE = {
    Person.First: CardAttributes.FirstPerson,
    Person.Second: CardAttributes.SecondPerson,
    Person.Third: CardAttributes.ThirdPerson}

GENDER_TO_ATTRIBUTE = {
    Gender.Masculine: CardAttributes.Masculine,
    Gender.Femanine: CardAttributes.Femanine,
    Gender.Neuter: CardAttributes.Neuter}

ATTRIBUTE_TO_GENDER = {
    CardAttributes.Masculine: Gender.Masculine,
    CardAttributes.Femanine: Gender.Femanine,
    CardAttributes.Neuter: Gender.Neuter}

VERB_SUFFIX_TO_ATTRIBUTE = {
    VerbSuffix.Ai: CardAttributes.VerbSuffixAi,
    VerbSuffix.Ei: CardAttributes.VerbSuffixEi,
    VerbSuffix.Ova: CardAttributes.VerbSuffixOva,
    VerbSuffix.Nu: CardAttributes.VerbSuffixNu,
    VerbSuffix.Nu2: CardAttributes.VerbSuffixNu2,
    VerbSuffix.A1: CardAttributes.VerbSuffixA1,
    VerbSuffix.A2: CardAttributes.VerbSuffixA2,
    VerbSuffix.A3: CardAttributes.VerbSuffixA3,
    VerbSuffix.Avai: CardAttributes.VerbSuffixAvai,
    VerbSuffix.O: CardAttributes.VerbSuffixO,
    VerbSuffix.I: CardAttributes.VerbSuffixI,
    VerbSuffix.E: CardAttributes.VerbSuffixE,
    VerbSuffix.Zha: CardAttributes.VerbSuffixZha,
    VerbSuffix.Resonant: CardAttributes.ResonantStem,
    VerbSuffix.Obstruent: CardAttributes.ObstruentStem,
}

ATTRIBUTE_NAMES = {
    CardAttributes.VerbSuffixAi:   "Suffix -ай",
    CardAttributes.VerbSuffixEi:   "Suffix -ей",
    CardAttributes.VerbSuffixOva:  "Suffix -ова",
    CardAttributes.VerbSuffixNu:   "Suffix -ну",
    CardAttributes.VerbSuffixNu2:  "Suffix -(ну)",
    CardAttributes.VerbSuffixA1:   "Suffix -а",
    CardAttributes.VerbSuffixA2:   "Suffix -а",
    CardAttributes.VerbSuffixA3:   "Suffix -а",
    CardAttributes.VerbSuffixAvai: "Suffix -авай",
    CardAttributes.VerbSuffixO:    "Suffix -о",
    CardAttributes.VerbSuffixI:    "Suffix -и",
    CardAttributes.VerbSuffixE:    "Suffix -е",
    CardAttributes.VerbSuffixZha:  "Suffix -жа",
    CardAttributes.ObstruentStem:  "Obstruent Stem",
    CardAttributes.ResonantStem:   "Resonant Stem",
    CardAttributes.VerbOfMotion:   "Verb of Motion",
    CardAttributes.AdjectiveAsNoun: "Adj. Used as Noun"
}

ATTRIBUTE_SHORT_DISPLAY_NAMES = {
    CardAttributes.VerbSuffixAi:   "-ай",
    CardAttributes.VerbSuffixEi:   "-ей",
    CardAttributes.VerbSuffixOva:  "-ова",
    CardAttributes.VerbSuffixNu:   "-ну",
    CardAttributes.VerbSuffixNu2:  "-(ну)",
    CardAttributes.VerbSuffixA1:   "-а",
    CardAttributes.VerbSuffixA2:   "-а",
    CardAttributes.VerbSuffixA3:   "-а",
    CardAttributes.VerbSuffixAvai: "-авай",
    CardAttributes.VerbSuffixO:    "-о",
    CardAttributes.VerbSuffixI:    "-и",
    CardAttributes.VerbSuffixE:    "-е",
    CardAttributes.VerbSuffixZha:  "-жа",
    CardAttributes.ObstruentStem:  "Obstr",
    CardAttributes.ResonantStem:   "Reson",
    CardAttributes.Masculine:      "M",
    CardAttributes.Neuter:         "N",
    CardAttributes.Femanine:       "F",
}

ATTRIBUTE_COLORS = {
    CardAttributes.Masculine: Color(255, 0, 0),
    CardAttributes.Femanine: Color(255, 128, 200),
    CardAttributes.Neuter: Color(128, 128, 128),
    CardAttributes.Perfective: Color(128, 0, 128),
    CardAttributes.Imperfective: Color(0, 160, 180),
    CardAttributes.Unidirectional: Color(0, 180, 0),
    CardAttributes.Multidirectional: Color(180, 180, 0),
    CardAttributes.Nominative: Color(50, 50, 50),
    CardAttributes.Accusative: Color(160, 0, 0),
    CardAttributes.Dative: Color(100, 0, 0),
    CardAttributes.Genetive: Color(80, 15, 0),
    CardAttributes.Prepositional: Color(0, 100, 0),
    CardAttributes.Instrumental: Color(100, 100, 0),
}

def get_card_attribute_display_name(attribute: CardAttributes):
     return ATTRIBUTE_NAMES.get(attribute, attribute.name)
