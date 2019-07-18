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
    """
    Calculate the history score given a list of pass/fail booleans.
    Lower indices represent the most recent entries.
    """
    if len(history) == 0:
        return 0.0
    score = 1.0
    for index, good in enumerate(history):
        if not good:
            score -= 0.5 / (index + 2)
    min_length = 6
    if len(history) < min_length:
        score /= (min_length - len(history) + 1.0)
    return score


class Card:
    """
    A card with English and Russian sides that can be studied.
    """

    def __init__(self, front="", back=""):
        self.word_type = None
        self.text = [front, back]
        self.attributes = [[], []]
        self.word_name = AccentedText(self.russian)
        self.examples = []
        self.source = None

        # CardStudyData
        self.proficiency_level = 0  # 0 = new/unseen
        self.history = []  # History of True or False markings
        self.last_encounter_time = None

        self.word = None

        # used by Scheduler
        self.rep = None
        self.age = 0

    def generate_word_name(self):
        """Generate the lits of word names from the card text."""
        self.word_name = AccentedText(self.russian)
        word_tokens = list(split_words(self.russian.text))
        if len(word_tokens) > 0:
            self.word_name = AccentedText(word_tokens[0][0])

    def get_word_names(self):
        """Get the list of word names associated with this card."""
        for name, index in split_words(self.russian.text):
            yield AccentedText(name)

    def get_key(self) -> tuple:
        """Get the key that identifies this card."""
        return (self.word_type, self.russian.text, self.english.text)

    def get_proficiency_score(self) -> float:
        """Get the key proficiency score."""
        return max(0.0, float(self.proficiency_level - 1) /
                   (Config.proficiency_levels - 1))

    def get_history_score(self) -> float:
        """Get the card's current history score."""
        return get_history_score(self.history)

    def get_next_history_score(self, knew_it: bool) -> float:
        """Get the card's next history score, given whether it was known or not."""
        history = [knew_it] + self.history
        return get_history_score(history[:Config.max_card_history_size])

    def add_attributes(self, attrs: list, side: CardSide):
        """Add multiple attributes to the card."""
        for attr in attrs:
            self.add_attribute(attr=attr, side=side)

    def add_attribute(self, attr: CardAttributes, side: CardSide):
        """Add an attribute to the card."""
        if attr not in self.attributes[side]:
            self.attributes[side].append(attr)
            self.attributes[side].sort(key=lambda x: x.name)

    def get_display_text(self, side: CardSide):
        """Get the text to display for a given side."""
        text = self.text[side]
        attributes = self.attributes[side]
        if len(attributes) > 0:
            text += " (" + ", ".join(a.value + "." for a in attributes) + ")"
        return text

    def get_word_type(self) -> WordType:
        return self.word_type

    def get_text(self, side: CardSide):
        """Get the text for a given side."""
        return self.text[side]

    def get_attributes(self, side: CardSide):
        """Get the card attributes for a given side."""
        return self.attributes[side]

    @property
    def english(self):
        """Get the card's English side text."""
        return self.text[CardSide.English]

    @property
    def russian(self):
        """Get the card's Russian side text."""
        return self.text[CardSide.Russian]

    @property
    def encountered(self):
        """Get whether the card has been encountered yet."""
        return self.last_encounter_time is not None

    def elapsed_time_string(self):
        """
        Get the string representing the time since the last encouder.
        example: "15 minutes ago".
        """
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
        """Serialize the card study data."""
        history_str = "".join("T" if h else "F" for h in self.history)
        return dict(type=None if self.word_type is None else self.word_type.name,
                    russian=repr(self.text[CardSide.Russian]),
                    english=repr(self.text[CardSide.English]),
                    proficiency_level=self.proficiency_level,
                    last_encounter_time=self.last_encounter_time,
                    history=history_str)

    def deserialize(self, state):
        """Deserialize the card study data."""
        self.proficiency_level = state["proficiency_level"]
        self.last_encounter_time = state["last_encounter_time"]
        history_str = state["history"]
        self.history = [c == "T" for c in history_str]
