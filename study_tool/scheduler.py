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


class ScheduleMode(IntEnum):
    Learning = 1
    NewOnly = 2


class ProficiencySet:
    def __init__(self, level, cards):
        self.cards = list(cards)
        self.rep = None
        self.level = level

    def remove(self, card):
        index = self.cards.index(card)
        if index < 0:
            raise Exception(card)
        del self.cards[index]

    def add(self, card):
        self.cards.append(card)

    def available_cards(self, rep, age):
        return [c for c in self.cards
                if c.rep is None or rep - c.rep >= age]


class Scheduler:
    """
    Handles scheduling the order of cards to study.
    """

    def __init__(self, cards, study_database, mode=ScheduleMode.Learning):
        cards = list(cards)
        self.mode = mode
        self.study_database = study_database

        self.proficiency_levels = Config.proficiency_levels
        self.proficiency_level_intervals = Config.proficiency_level_intervals
        self.new_card_interval = Config.new_card_interval
        self.min_repeat_interval = Config.min_repeat_interval

        self.sets = {}
        for level in range(0, self.proficiency_levels + 1):
            self.sets[level] = ProficiencySet(level=level, cards=[])
        for card in cards:
            card.rep = None
            study_data = self.study_database.get_card_study_data(card)
            self.sets[study_data.get_proficiency_level()].add(card)

        self.rep = 0

    def get_all_cards(self):
        for proficiency_set in self.sets.values():
            for card in proficiency_set.cards:
                yield card

    def mark(self, card: Card, knew_it: bool):
        study_data = self.study_database.get_card_study_data(card)
        self.sets[study_data.get_proficiency_level()].remove(card)
        self.study_database.mark_card(card, knew_it)
        self.sets[study_data.get_proficiency_level()].add(card)
        card.rep = self.rep

    def next(self) -> Card:
        card = self.__get_next_card()
        self.rep += 1
        return card

    def __get_next_card(self) -> Card:
        card = None

        if self.mode == ScheduleMode.NewOnly:
            card = self.__get_new_card()
            return card

        if self.rep % self.new_card_interval == 0:
            card = self.__get_new_card()
            if card is not None:
                return card

        for min_interval in range(self.min_repeat_interval, -1, -1):
            available_sets = {}
            for proficiency_set in self.sets.values():
                if proficiency_set.level != 0:
                    cards = proficiency_set.available_cards(
                        self.rep, min_interval)
                    if len(cards) > 0:
                        available_sets[proficiency_set] = cards

            if len(available_sets) > 0:
                next_set = choose_weighted_by_age(
                    list(available_sets.keys()), rep=self.rep)
                card = choose_weighted_by_age(
                    available_sets[next_set], rep=self.rep)
                return card

            card = self.__get_new_card()
            if card is not None:
                return card

        return None

    def __get_new_card(self) -> Card:
        if len(self.sets[0].cards) == 0:
            return None
        card = choose(self.sets[0].cards)
        card.rep = self.rep
        return card
