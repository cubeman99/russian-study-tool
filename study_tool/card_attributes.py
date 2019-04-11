from enum import Enum, IntEnum
import os
import time
from study_tool.config import Config
from study_tool.russian.word import *
from cmg.graphics import color
  
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
  Nominative =  "nom"
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

RUSSIAN_SIDE_ATTRIBUTES = [
  CardAttributes.Short,
  CardAttributes.Long,
  CardAttributes.Transative,
  CardAttributes.Intransative,
  CardAttributes.Animate,
  CardAttributes.Inanimate,
  ]

VERB_SUFFIX_TO_ATTRIBUTE = {
  VerbSuffix.Ai  : CardAttributes.VerbSuffixAi,  
  VerbSuffix.Ei  : CardAttributes.VerbSuffixEi,  
  VerbSuffix.Ova : CardAttributes.VerbSuffixOva, 
  VerbSuffix.Nu  : CardAttributes.VerbSuffixNu,  
  VerbSuffix.Nu2 : CardAttributes.VerbSuffixNu2, 
  VerbSuffix.A1  : CardAttributes.VerbSuffixA1,   
  VerbSuffix.A2  : CardAttributes.VerbSuffixA2,   
  VerbSuffix.A3  : CardAttributes.VerbSuffixA3,   
  VerbSuffix.Avai: CardAttributes.VerbSuffixAvai,
  VerbSuffix.O   : CardAttributes.VerbSuffixO,   
  VerbSuffix.I   : CardAttributes.VerbSuffixI,   
  VerbSuffix.E   : CardAttributes.VerbSuffixE,
  VerbSuffix.Zha : CardAttributes.VerbSuffixZha,   
  VerbSuffix.Resonant  : CardAttributes.ResonantStem,
  VerbSuffix.Obstruent : CardAttributes.ObstruentStem,
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

ATTRIBUTE_COLORS = {
  CardAttributes.Masculine: color.rgb(255, 0, 0),
  CardAttributes.Femanine: color.rgb(255, 128, 200),
  CardAttributes.Neuter: color.rgb(128, 128, 128),
  CardAttributes.Perfective: color.rgb(128, 0, 128),
  CardAttributes.Imperfective: color.rgb(0, 160, 180),
  CardAttributes.Unidirectional: color.rgb(0, 180, 0),
  CardAttributes.Multidirectional: color.rgb(180, 180, 0),
  CardAttributes.Nominative: color.gray(50),
  CardAttributes.Accusative: color.rgb(160, 0, 0),
  CardAttributes.Dative: color.rgb(100, 0, 0),
  CardAttributes.Genetive: color.rgb(80, 15, 0),
  CardAttributes.Prepositional: color.rgb(0, 100, 0),
  CardAttributes.Instrumental: color.rgb(100, 100, 0),
  }
