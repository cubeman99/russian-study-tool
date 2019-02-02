from enum import Enum, IntEnum
import os
import time
from study_tool.config import Config

class CardSide(IntEnum):
  Russian = 0
  English = 1
  
class CardAttributes(Enum):
  Masculine = "m"
  Femanine = "f"
  Neuter = "n"
  Singular = "sing"
  Plural = "pl"
  NoPural = "nopl"
  FirstPerson = "1st"
  SecondPerson = "2nd"
  ThirdPerson = "3rd"
  Perfective = "pf"
  Imperfective = "impf"
  Informal = "infl"
  Formal = "frml"
  Unidirectional = "uni"
  Multidirectional = "multi"
  Nominative =  "nom"
  Accusative = "acc"
  Genetive = "gen"
  Dative = "dat"
  Prepositional = "prep"
  Instrumental = "instr"
  Indeclinable = "indec"
  Animate = "anim"
  Inanimate = "inanim"

class Card:
  def __init__(self, front="", back=""):
    self.text = [front, back]
    self.attributes = [[], []]
    self.marked = False
    self.last_encounter_time = None
    self.proficiency_level = 0  # new/unseen
    self.history = []  # History of True or False markings

    self.rep = None  # used by Scheduler
    self.age = 0

  def get_display_text(self, side):
    text = self.text[side]
    attributes = self.attributes[side]
    if len(attributes) > 0:
      text += " (" + ", ".join(a.value + "." for a in attributes) + ")"
    return text

  @property
  def english(self):
    return self.text[CardSide.English]

  @property
  def russian(self):
    return self.text[CardSide.Russian]

  @property
  def encountered(self):
    return self.last_encounter_time is not None

  def elapsed_time_string(self):
    elapsed_time = time.time() - self.last_encounter_time
    units = "second"
    if elapsed_time > 60:
      units = "minute"
      elapsed_time /= 60
      if elapsed_time > 60:
        units = "hour"
        elapsed_time /= 60
        if elapsed_time > 24:
          units = "day"
          elapsed_time /= 24
    elapsed_time = int(round(elapsed_time))
    return "{} {}{} ago".format(elapsed_time, units,
                                "s" if elapsed_time != 1 else "")

  def serialize(self):
    history_str = "".join("T" if h else "F" for h in self.history)
    return dict(russian=self.text[CardSide.Russian],
                english=self.text[CardSide.English],
                marked=self.marked,
                proficiency_level=self.proficiency_level,
                last_encounter_time=self.last_encounter_time,
                history=history_str)

  def deserialize(self, state):
    self.text[CardSide.Russian] = state["russian"]
    self.text[CardSide.English] = state["english"]
    self.proficiency_level = state["proficiency_level"]
    self.marked = state["marked"]
    self.last_encounter_time = state["last_encounter_time"]
    history_str = state["history"]
    self.history = [c == "T" for c in history_str]
  