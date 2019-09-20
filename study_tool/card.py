from enum import Enum, IntEnum
import os
import time
from study_tool.config import Config
from study_tool.russian.word import *
from study_tool.russian.word import WordType
from study_tool.russian.word import WordPattern
from study_tool.card_attributes import CardAttributes, ENGLISH_SIDE_CARD_ATTRIBUTES


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


STRING_TO_WORD_TYPE_DICT = {"none": WordType.Other,
                            None: WordType.Other}
for word_type in WordType:
    STRING_TO_WORD_TYPE_DICT[word_type.name.lower()] = word_type


class Card:
    """
    A card with English and Russian sides that can be studied.
    """

    def __init__(self, front="", back=""):
        self.word_type = None
        self.text = [AccentedText(front), AccentedText(back)]
        self.__attributes = []
        self.word_name = AccentedText(self.russian)
        self.examples = []
        self.related_cards = []
        self.source = None
        self.__fixed_card_set = None
        self.__word_patterns = []

        self.word = None
        self.__study_data = None

        # used by Scheduler
        self.rep = None
        self.age = 0

    def get_word(self):
        return self.word

    def get_study_data(self):
        return self.__study_data

    def get_word_patterns(self) -> list:
        return self.__word_patterns

    def get_fixed_card_set(self):
        return self.__fixed_card_set

    def get_word_names(self):
        """Get the list of word names associated with this card."""
        for name, index in split_words(self.russian.text):
            yield AccentedText(name)

    def get_key(self) -> tuple:
        """Get the key that identifies this card."""
        return (self.word_type,
                self.russian.text.lower(),
                self.english.text.lower())

    def get_english_key(self) -> tuple:
        return (self.word_type, self.english.text.lower(),
                ",".join(sorted([x.value for x in self.get_attributes() if x in ENGLISH_SIDE_CARD_ATTRIBUTES])))

    def get_russian_key(self) -> tuple:
        return (self.word_type, self.russian.text.lower(),
                ",".join(sorted([x.value for x in self.get_attributes()])))

    def is_in_fixed_card_set(self) -> bool:
        return self.__fixed_card_set is not None

    def set_fixed_card_set(self, card_set):
        self.__fixed_card_set = card_set

    def set_study_data(self, study_data):
        self.__study_data = study_data

    def generate_word_name(self):
        """Generate the lits of word names from the card text."""
        self.word_name = AccentedText(self.russian)
        word_tokens = list(split_words(self.russian.text))
        if len(word_tokens) > 0:
            self.word_name = AccentedText(word_tokens[0][0])
        self.__word_patterns = []
        for text in self.russian.text.split(";"):
            tokens = list(x for x, _ in split_words(self.russian.text))
            pattern = WordPattern(tokens)
            self.__word_patterns.append(pattern)
    
    def clear_attributes(self):
        """Clear all card attributes."""
        self.__attributes = []
    
    def clear_related_cards(self):
        """Clear all related cards."""
        self.related_cards = []

    def add_attributes(self, attrs: list):
        """Add multiple attributes to the card."""
        for attr in attrs:
            self.add_attribute(attr)

    def add_attribute(self, attr: CardAttributes):
        """Add an attribute to the card."""
        if attr not in self.__attributes:
            self.__attributes.append(attr)
            self.__attributes.sort(key=lambda x: x.name)

    def get_display_text(self, side: CardSide):
        """Get the text to display for a given side."""
        text = self.text[side]
        if self.__attributes and side == CardSide.Russian:
            text += " (" + ", ".join(a.value + "." for a in self.__attributes) + ")"
        return text

    def get_word_type(self) -> WordType:
        return self.word_type

    def get_russian(self) -> AccentedText:
        return self.russian

    def get_english(self) -> AccentedText:
        return self.english

    def get_text(self, side: CardSide):
        """Get the text for a given side."""
        return self.text[side]

    def get_attributes(self, side=None) -> list:
        """Get the card attributes for a given side."""
        return self.__attributes

    def get_related_cards(self) -> list:
        """Get the list of related cards."""
        return self.related_cards

    @property
    def english(self):
        """Get the card's English side text."""
        return self.text[CardSide.English]

    @property
    def russian(self):
        """Get the card's Russian side text."""
        return self.text[CardSide.Russian]

    def set_english(self, english: AccentedText):
        """Set the english text."""
        self.text[CardSide.English] = AccentedText(english)
        
    def set_russian(self, russian: AccentedText):
        """Set the russian text."""
        self.text[CardSide.Russian] = AccentedText(russian)
        
    def set_word_type(self, word_type: WordType):
        """Set the card type."""
        self.word_type = word_type

    def add_related_card(self, related_card):
        if related_card not in self.related_cards:
            self.related_cards.append(related_card)

    def remove_related_card(self, related_card):
        if related_card in self.related_cards:
            self.related_cards.remove(related_card)

    def serialize_card_data(self):
        """Serialize the card data."""
        state = {}
        state["type"] = self.word_type.name.lower()
        state["en"] = repr(self.english)
        state["ru"] = repr(self.russian)
        if self.__attributes:
            state["attrs"] = [x.value for x in self.__attributes]
        if self.examples:
            state["ex"] = [[repr(e), ""] for e in self.examples]
        if self.related_cards:
            state["rel"] = []
            for related_card in self.related_cards:
                state["rel"].append([
                    related_card.get_word_type().name.lower(),
                    related_card.get_russian().text.lower(),
                    related_card.get_english().text.lower()])
        return state

    def deserialize_card_data(self, state):
        """Deserialize the card data."""
        self.text[CardSide.Russian] = AccentedText(state["ru"])
        self.text[CardSide.English] = AccentedText(state["en"])
        self.word_type = STRING_TO_WORD_TYPE_DICT[state["type"].lower()]
        self.examples = []
        if "ex" in state:
            for en, ru in state["ex"]:
                self.examples.append(AccentedText(en))
        self.__attributes = []
        if "attrs" in state:
            for attr_short in state["attrs"]:
                attr = CardAttributes(attr_short)
                self.add_attribute(attr)
        self.related_cards = []  # Card database deserializes these
               
    def __repr__(self):
        attrs = "|".join(sorted([x.value for x in self.get_attributes()]))
        return "Card({}, '{}', '{}', '{}')".format(
            self.word_type.name if self.word_type is not None else "None",
            repr(self.english),
            repr(self.russian),
            attrs)
