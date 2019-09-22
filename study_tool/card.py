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


class Card:
    """
    A card with English and Russian sides that can be studied.
    """

    __STRING_TO_WORD_TYPE_DICT = {"none": WordType.Other,
                                  None: WordType.Other}
    for word_type in WordType:
        __STRING_TO_WORD_TYPE_DICT[word_type.name.lower()] = word_type

    def __init__(self, russian=None, english=None, word_type=None,
                 related_cards=None, attributes=None, examples=None,
                 copy=None):
        """
        Constructs a new card.
        """
        if copy is not None:
            self.set(copy)
        else:
            # Word data
            self.__word_type = None
            self.__russian = AccentedText("")
            self.__english = AccentedText("")
            self.__card_attributes = []
            self.__examples = []
            self.__related_cards = []

        if word_type is not None:
            self.__word_type = word_type
        if russian is not None:
            self.__russian = AccentedText(russian)
        if english is not None:
            self.__english = AccentedText(english)
        if attributes is not None:
            self.__card_attributes = list(attributes)
        if examples is not None:
            self.__examples = list(examples)
        if related_cards is not None:
            self.__related_cards = list(related_cards)

        # Cached data
        self.source = None
        self.__fixed_card_set = None
        self.__word_patterns = []
        self.word_name = AccentedText(self.__russian)
        self.word = None
        self.__study_data = None

        # used by Scheduler
        self.rep = None
        self.age = 0

    def set(self, other):
        """Sets the card data based on a copy."""
        self.__word_type = other.get_word_type()
        self.__russian = AccentedText(other.get_russian())
        self.__english = AccentedText(other.get_english())
        self.__card_attributes = list(other.get_attributes())
        self.__examples = list(other.get_examples())
        self.__related_cards = list(other.get_related_cards())

    def clone(self):
        """Returns a copy of this card."""
        return Card(copy=self)

    def get_word(self):
        return self.word

    def get_study_data(self):
        return self.__study_data

    def get_word_patterns(self) -> list:
        return self.__word_patterns

    def get_fixed_card_set(self):
        return self.__fixed_card_set

    def get_examples(self) -> list:
        return self.__examples

    def get_word_names(self):
        """Get the list of word names associated with this card."""
        for name, index in split_words(self.__russian.text):
            yield AccentedText(name)

    def get_key(self) -> tuple:
        """Get the key that identifies this card."""
        return (self.__word_type,
                self.__russian.text.lower(),
                self.__english.text.lower())

    def get_english_key(self) -> tuple:
        """
        Returns the key that identifies the Russian translation
        from English text.
        """
        return (self.__word_type, self.__english.text.lower(),
                ",".join(sorted(self.get_english_attributes())))
    
    def get_english_attributes(self) -> list:
        """
        Gets the list of card attributes to show along with the English text.
        """
        return [x.value for x in self.get_attributes()
                if x in ENGLISH_SIDE_CARD_ATTRIBUTES]

    def get_russian_key(self) -> tuple:
        """
        Returns the key that identifies the English translation
        from Russian text.
        """
        return (self.__word_type, self.__russian.text.lower())

    def is_in_fixed_card_set(self) -> bool:
        return self.__fixed_card_set is not None

    def set_fixed_card_set(self, card_set):
        self.__fixed_card_set = card_set

    def set_study_data(self, study_data):
        self.__study_data = study_data

    def generate_word_name(self):
        """Generate the lits of word names from the card text."""
        self.word_name = AccentedText(self.__russian)
        word_tokens = list(split_words(self.__russian.text))
        if len(word_tokens) > 0:
            self.word_name = AccentedText(word_tokens[0][0])

        self.__word_patterns = []
        for text in self.__russian.text.split(";"):
            tokens = list(x for x, _ in split_words(self.__russian.text))
            pattern = WordPattern(tokens)
            self.__word_patterns.append(pattern)
    
    def clear_attributes(self):
        """Clear all card attributes."""
        self.__card_attributes = []
    
    def set_attributes(self, attributes: list):
        """Sets all card attributes."""
        self.__card_attributes = list(attributes)

    def add_attributes(self, attrs: list):
        """Add multiple attributes to the card."""
        for attr in attrs:
            self.add_attribute(attr)

    def add_attribute(self, attr: CardAttributes):
        """Add an attribute to the card."""
        if attr not in self.__card_attributes:
            self.__card_attributes.append(attr)
            self.__card_attributes.sort(key=lambda x: x.name)

    def clear_related_cards(self):
        """Clear all related cards."""
        self.__related_cards = []
    
    def set_related_cards(self, related_cards: list):
        """Sets the list of related cards."""
        self.__related_cards = list(related_cards)
    
    def set_examples(self, examples: list):
        """Sets all card examples."""
        self.__examples = list(examples)

    def add_example(self, russian):
        """Add an example to the card."""
        self.__examples.append(AccentedText(russian))

    def get_display_text(self, side: CardSide):
        """Get the text to display for a given side."""
        text = self.get_text(side)
        if self.__card_attributes and side == CardSide.Russian:
            text += " (" + ", ".join(a.value + "." for a in self.__card_attributes) + ")"
        return text

    def get_word_type(self) -> WordType:
        """Get the card's word type."""
        return self.__word_type

    def get_russian(self) -> AccentedText:
        """Get the card's Russian side text."""
        return self.__russian

    def get_english(self) -> AccentedText:
        """Get the card's English side text."""
        return self.__english

    def get_text(self, side: CardSide):
        """Get the text for a given side."""
        if side == CardSide.English:
            return self.__english
        if side == CardSide.Russian:
            return self.__russian
        raise KeyError(side)

    def get_attributes(self, side=None) -> list:
        """Get the card attributes for a given side."""
        return self.__card_attributes

    def get_related_cards(self) -> list:
        """Get the list of related cards."""
        return self.__related_cards

    def set_english(self, english: AccentedText):
        """Set the english text."""
        self.__english = AccentedText(english)
        
    def set_russian(self, russian: AccentedText):
        """Set the russian text."""
        self.__russian = AccentedText(russian)
        
    def set_word_type(self, word_type: WordType):
        """Set the card type."""
        self.__word_type = word_type

    def add_related_card(self, related_card):
        if related_card not in self.__related_cards:
            self.__related_cards.append(related_card)

    def remove_related_card(self, related_card):
        if related_card in self.__related_cards:
            self.__related_cards.remove(related_card)

    def serialize_card_data(self):
        """Serialize the card data."""
        state = {}
        state["type"] = self.__word_type.name.lower()
        state["en"] = repr(self.__english)
        state["ru"] = repr(self.__russian)
        if self.__card_attributes:
            state["attrs"] = [x.value for x in self.__card_attributes]
        if self.__examples:
            state["ex"] = [[repr(e), ""] for e in self.__examples]
        if self.__related_cards:
            state["rel"] = []
            for related_card in self.__related_cards:
                state["rel"].append([
                    related_card.get_word_type().name.lower(),
                    related_card.get_russian().text.lower(),
                    related_card.get_english().text.lower()])
        return state

    def deserialize_card_data(self, state):
        """Deserialize the card data."""
        self.__russian = AccentedText(state["ru"])
        self.__english = AccentedText(state["en"])
        self.__word_type = self.__STRING_TO_WORD_TYPE_DICT[state["type"].lower()]
        self.__examples = []
        if "ex" in state:
            for en, ru in state["ex"]:
                self.__examples.append(AccentedText(en))
        self.__card_attributes = []
        if "attrs" in state:
            for attr_short in state["attrs"]:
                attr = CardAttributes(attr_short)
                self.add_attribute(attr)
        self.__related_cards = []  # Card database deserializes these
               
    def __repr__(self):
        attrs = "|".join(sorted([x.value for x in self.get_attributes()]))
        return "Card({}, '{}', '{}', '{}')".format(
            self.__word_type.name if self.__word_type is not None else "None",
            repr(self.__english),
            repr(self.__russian),
            attrs)
