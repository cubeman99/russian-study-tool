import os
import random
import re
import time
from study_tool.card import Card, CardSide, SourceLocation
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config


class CardGroupMetrics:
    def __init__(self):
        self.history_score = 0.0
        self.proficiency_counts = []
        for level in range(0, Config.proficiency_levels + 1):
            self.proficiency_counts.append(0)

    def get_total_count(self):
        return sum(self.proficiency_counts)

    def get_proficiency_percent(self):
        score = 0
        potential_score = 0
        for level, count in enumerate(self.proficiency_counts):
            score += count * Config.proficiency_level_score_multiplier[level]
            potential_score += count
        return score / potential_score

    def get_proficiency_count(self):
        return self.get_proficiency_percent() * self.get_total_count()

    def serialize(self):
        return {"history_score": self.history_score,
                "proficiency_counts": self.proficiency_counts}

    def deserialize(self, state):
        self.history_score = state["history_score"]
        self.proficiency_counts = list(state["proficiency_counts"])


class StudySet:
    def __init__(self, name="", cards=()):
        self.name = AccentedText(name)
        self.cards = list(cards)

    def get_name(self) -> AccentedText:
        return self.name

    def get_cards(self) -> list:
        return self.cards

    def get_card_count(self) -> int:
        return len(self.cards)

    def has_card(self, card: Card) -> bool:
        return card in self.cards

    def set_name(self, name: AccentedText):
        self.name = AccentedText(name)

    def add_card(self, card: Card):
        self.cards.append(card)

    def remove_card(self, card: Card):
        self.cards.remove(card)

    def set_cards(self, cards: list):
        self.cards = list(cards)

    def clear(self):
        self.cards = []

    def get_study_metrics(self):
        metrics = CardGroupMetrics()
        metrics.history_score = sum(c.get_history_score() for c in self.cards)
        for level in range(0, Config.proficiency_levels + 1):
            metrics.proficiency_counts[level] = len(
                [c for c in self.cards if c.proficiency_level == level])
        return metrics

    def get_problem_cards(self):
        cs = sorted(self.cards, key=lambda c: c.get_history_score())
        for c in reversed(cs):
            history_preview_len = 16
            history_preview = ""
            for i in range(min(history_preview_len, len(c.history))):
                history_preview += "." if c.history[i] else "x"
            history_preview += " " * \
                (history_preview_len - len(history_preview))
            print("{:.4f} : {:3} [{}] {}".format(c.get_history_score(),
                                                 len(c.history),
                                                 history_preview,
                                                 c.russian,
                                                 c.english))
        return StudySet(name=self.name,
                        cards=[c for c in self.cards
                               if len(c.history) < 5
                               or c.get_history_score() < 0.9])

    def __repr__(self):
        return "StudySet<{} cards>".format(len(self.cards))


class CardSet(StudySet):
    def __init__(self, cards=(), fixed_card_set=False):
        StudySet.__init__(self, name="Untitled", cards=cards)
        self.key = None
        self.path = ""
        self.info = ""
        self.side = CardSide.English
        self.source = None
        self.__file_path = None
        self.__is_fixed_card_set = fixed_card_set

    def get_file_path(self) -> str:
        return self.__file_path

    def set_file_path(self, path: str):
        self.__file_path = path

    def set_fixed_card_set(self, fixed: bool):
        self.__is_fixed_card_set = fixed
        for card in self.cards:
            if fixed:
                card.set_fixed_card_set(self)
            else:
                card.set_fixed_card_set(None)

    def is_fixed_card_set(self) -> bool:
        return self.__is_fixed_card_set

    def next(self, seen, unseen):
        index = random.randint(0, len(unseen) - 1)
        card = unseen[index]
        del unseen[index]
        return card

    def serialize(self) -> dict:
        state = {
            "name": repr(self.name),
            "version": 1,
            "cards": []
        }
        for card in self.cards:
            state["cards"].append(
                [card.get_word_type().name.lower(),
                 card.get_russian().text,
                 card.get_english().text])
        return {"card_set": state}

    def __repr__(self):
        return "CardSet(\"{}\")".format(self.get_name())

            


class CardSetPackage(StudySet):
    def __init__(self, name, path, parent=None):
        # NOTE: Purposefully avoiding super __init__ here
        self.name = AccentedText(name)
        self.path = path
        self.parent = parent
        self.card_sets = []
        self.packages = []

    def get_parent(self):
        return self.parent

    def get_packages(self) -> list:
        return self.packages

    def get_card_sets(self) -> list:
        return self.card_sets

    def all_card_sets(self):
        for package in self.packages:
            for card_set in package.all_card_sets():
                yield card_set
        for card_set in self.card_sets:
            yield card_set

    @property
    def cards(self):
        for card_set in self.all_card_sets():
            for card in card_set.cards:
                yield card

    def add_card_set(self, card_set: CardSet):
        self.card_sets.append(card_set)

    def __getitem__(self, name):
        for package in self.packages:
            if package.name == name:
                return package
        for card_set in self.card_sets:
            if card_set.key == name:
                return card_set
        raise KeyError(name)

    def __repr__(self):
        return "CardSetPackage(\"{}\")".format(self.get_name())
