from enum import Enum, IntEnum
import os
import time
from study_tool.config import Config
from study_tool.russian.word import *
from study_tool.card_attributes import CardAttributes
from cmg.graphics import color

class CardSide(IntEnum):
  Russian = 0
  English = 1

class SourceLocation:
  def __init__(self, filename="", line_number=0, line_text=""):
    self.filename = filename
    self.line_number = line_number
    self.line_text = line_text
  def __str__(self):
    return "{}-{}".format(self.filename, self.line_number)

def get_history_score(history):
  score = 1
  for index, good in enumerate(history):
    if not good:
      score -= 1.0 / (index + 2)
  return score

class Card:
  def __init__(self, front="", back=""):
    self.text = [front, back]
    self.attributes = [[], []]
    self.marked = False
    self.last_encounter_time = None
    self.proficiency_level = 0  # new/unseen
    self.history = []  # History of True or False markings
    self.word_type = None
    self.word = None
    self.source = None

    # used by Scheduler
    self.rep = None
    self.age = 0

  def get_key(self):
    return (self.word_type, self.russian.text, self.english.text)

  def get_history_score(self):
    return get_history_score(self.history)

  def get_next_history_score(self, knew_it):
    history = [knew_it] + self.history
    return get_history_score(history[:Config.max_card_history_size])
  
  def add_attributes(self, attrs: list, side: CardSide):
    for attr in attrs:
      self.add_attribute(attr=attr, side=side)

  def add_attribute(self, attr: CardAttributes, side: CardSide):
    if attr not in self.attributes[side]:
      self.attributes[side].append(attr)
      self.attributes[side].sort(key=lambda x: x.name)

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
    return dict(russian=repr(self.text[CardSide.Russian]),
                english=repr(self.text[CardSide.English]),
                marked=self.marked,
                proficiency_level=self.proficiency_level,
                last_encounter_time=self.last_encounter_time,
                history=history_str)

  def deserialize(self, state):
    self.text[CardSide.Russian] = AccentedText(state["russian"])
    self.text[CardSide.English] = AccentedText(state["english"])
    self.proficiency_level = state["proficiency_level"]
    self.marked = state["marked"]
    self.last_encounter_time = state["last_encounter_time"]
    history_str = state["history"]
    self.history = [c == "T" for c in history_str]
  