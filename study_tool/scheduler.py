from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import *
from study_tool.card_set import *
from study_tool.config import Config


def choose(cards):
    if len(cards) == 0:
        return None
    return cards[random.randint(0, len(cards) - 1)]


def choose_weighted(cards, key=lambda card: 1):
    if len(cards) == 0:
        return None
    total_odds = 0
    choices = []
    for index, card in enumerate(cards):
        odds = key(card)
        total_odds += odds
        choices.append((total_odds, index))
    odds_index = random.randint(0, total_odds - 1)
    picked_index = None
    for odds, index in choices:
        if odds_index < odds:
            picked_index = index
            break
    return cards[picked_index]


def choose_weighted_by_age(values, rep):
    if len(values) == 0:
        return None
    elif all(x.rep is None for x in values):
        return choose(values)
    elif any(x.rep is None for x in values):
        return choose([x for x in values if x.rep is None])
    else:
        return choose_weighted(values,
                               key=lambda x: max(1, (rep - x.rep) * (rep - x.rep)))


class SchedulerParams:
    def __init__(self, max_repetitions=0):
        """
        :param max_repetitions: Max number of times a card can be shown, 0 for infinite.
        """
        self.max_repetitions = max_repetitions


class ProficiencySet:
    def __init__(self, level, cards=()):
        self.cards = set(cards)
        self.rep = None
        self.level = level

    def remove(self, card):
        assert card in self.cards
        self.cards.remove(card)

    def add(self, card):
        self.cards.add(card)

    def available_cards(self, rep, age):
        return [c for c in self.cards
                if c.rep is None or rep - c.rep >= age]


class CardSchedulingInfo:
    def __init__(self, card: Card, study_data):
        self.card = card
        self.study_data = study_data
        self.rep = None
        self.shown_count = 0


class Scheduler:
    """
    Handles scheduling the order of cards to study.
    """

    def __init__(self, cards, study_database, params=None):
        """
        Constructs the scheduler.
        """
        self.__study_database = study_database
        self.__params = params
        if params is None:
            self.__params = SchedulerParams()
           
        self.proficiency_level_intervals = Config.proficiency_level_intervals
        self.new_card_interval = Config.new_card_interval
        self.min_repeat_interval = Config.min_repeat_interval

        # Create card info
        self.__card_info_dict = {}
        self.__cards = set()
        for card in cards:
            study_data = self.__study_database.get_card_study_data(card)
            info = CardSchedulingInfo(card=card, study_data=study_data)
            self.__cards.add(info)
            self.__card_info_dict[card] = info

        # Group cards into proficiency sets
        self.__sets = {}
        for level in range(0, Config.proficiency_levels + 1):
            self.__sets[level] = ProficiencySet(level=level)
        for card in self.__cards:
            self.__sets[card.study_data.get_proficiency_level()].add(card)

        self.__rep = 0

    def reset(self):
        """Reset the scheduler."""
        for level in range(0, Config.proficiency_levels + 1):
            self.__sets[level] = ProficiencySet(level=level, cards=[])
        for card in self.__cards:
            self.__sets[card.study_data.get_proficiency_level()].add(card)
        self.__rep = 0

    def mark(self, card: Card, knew_it: bool):
        """Mark a card as "knew it" or "didn't know it"."""
        info = self.__card_info_dict[card]
        self.__sets[info.study_data.get_proficiency_level()].remove(info)
        self.__study_database.mark_card(card, knew_it)
        self.__sets[info.study_data.get_proficiency_level()].add(info)
        info.rep = self.__rep
        info.shown_count += 1

        # Check if we have shown this card too many times
        if (self.__params.max_repetitions > 0 and
                info.shown_count >= self.__params.max_repetitions):
            self.__sets[info.study_data.get_proficiency_level()].remove(info)

    def next(self) -> Card:
        """Get the next scheduled card."""
        info = self.__get_next_card()
        self.__rep += 1
        return info.card if info else None

    def __get_next_card(self) -> CardSchedulingInfo:
        """Get the next scheduled CardSchedulingInfo."""
        card = None

        # Show a new card every new card interval
        if self.__rep % self.new_card_interval == 0:
            card = self.__get_new_card()
            if card is not None:
                return card

        for min_interval in range(self.min_repeat_interval, -1, -1):
            available_sets = {}
            for proficiency_set in self.__sets.values():
                if proficiency_set.level != 0:
                    cards = proficiency_set.available_cards(
                        self.__rep, min_interval)
                    if len(cards) > 0:
                        available_sets[proficiency_set] = cards

            if len(available_sets) > 0:
                next_set = choose_weighted_by_age(
                    list(available_sets.keys()), rep=self.__rep)
                card = choose_weighted_by_age(
                    available_sets[next_set], rep=self.__rep)
                return card

            card = self.__get_new_card()
            if card is not None:
                return card

        return None

    def __get_new_card(self) -> CardSchedulingInfo:
        """Returns the next scheduled 'new' CardSchedulingInfo."""
        if not self.__sets[0].cards:
            return None
        return choose(self.__sets[0].cards)
