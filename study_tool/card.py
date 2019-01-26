from enum import IntEnum
import os
import time

class CardSide(IntEnum):
  Russian = 0
  English = 1

class Card:
  def __init__(self, front, back):
    self.text = [front, back]
    self.marked = False
    self.last_encounter_time = None
    self.proficiency_level = 0  # new/unseen

    self.rep = None  # used by Scheduler
    self.age = 0

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

  def encounter(self):
    self.age = 0

  def mark(self):
    self.marked = True
    self.last_encounter_time = time.time()
    
  def skip(self):
    self.marked = False
    self.last_encounter_time = time.time()

  def serialize(self):
    return dict(russian=self.text[CardSide.Russian],
                english=self.text[CardSide.English],
                marked=self.marked,
                age=self.age,
                proficiency_level=self.proficiency_level,
                last_encounter_time=self.last_encounter_time)

  def deserialize(self, state):
    self.text[CardSide.Russian] = state["russian"]
    self.text[CardSide.English] = state["english"]
    self.proficiency_level = state["proficiency_level"]
    self.marked = state["marked"]
    self.last_encounter_time = state["last_encounter_time"]
    self.age = state["age"]
  