from enum import IntEnum
import os
import pygame
import random
import re
import time
import traceback
from cmg import color
from cmg import math
from cmg import widgets
from cmg.color import Colors
from cmg.event import Event
from study_tool.russian.types import WordType
from study_tool.card import Card
from study_tool.card_set import StudySet
from study_tool.card import CardSide
from study_tool.query import CardQuery
from study_tool.gui.card_list_table import CardListTable
from study_tool.config import Config
from study_tool.states.study_state import StudyParams

class SortMethod:
    RANDOM = "Random"
    LOWEST_SCORE = "Lowest Score"
    OLDEST = "Oldest"
    NEWEST = "Newest"


class QueryWidget(widgets.Widget):
    """
    Widget for editing a study query.
    """

    def __init__(self, application):
        super().__init__()
        self.__application = application
        self.__card_database = application.card_database
        self.__study_database = application.card_database
        self.__cards = []
        self.__study_params = None

        card_type_options = ["Any"]
        card_type_options += [x.name for x in WordType]

        # Create widgets
        self.__table_cards = CardListTable(select_text="+")
        self.__box_count = widgets.TextEdit("60")
        self.__combo_proficiency = widgets.ComboBox(["New", "Red", "Orange", "Yellow", "Any"], index=4)
        self.__box_score = widgets.TextEdit("1.0")
        self.__combo_card_type = widgets.ComboBox(card_type_options, index=0)
        self.__label_result_count = widgets.Label("<result-count>")
        self.__combo_side = widgets.ComboBox(["Any", "English", "Russian"], index=0)
        self.__checkbox_random_forms = widgets.CheckBox("Random Forms", checked=False)
        self.__checkbox_only_once = widgets.CheckBox("Only Show Once", checked=False)
        self.__combo_sort = widgets.ComboBox([SortMethod.RANDOM, SortMethod.LOWEST_SCORE,
                                              SortMethod.NEWEST, SortMethod.OLDEST], index=0)
        self.__button_begin = widgets.Button("Begin")

        # Create layouts
        layout_left = widgets.VBoxLayout()
        layout_left.add(widgets.Label("Card Filter:"))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Max Count:"), self.__box_count))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Max Level:"), self.__combo_proficiency))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Max Score:"), self.__box_score))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Type:"), self.__combo_card_type))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Sort By:"), self.__combo_sort))
        layout_left.add(widgets.Label("Study Settings:"))
        layout_left.add(widgets.HBoxLayout(widgets.Label("Show Side:"), self.__combo_side))
        layout_left.add(self.__checkbox_random_forms)
        layout_left.add(self.__checkbox_only_once)
        layout_left.add(self.__button_begin)
        layout_right = widgets.VBoxLayout()
        layout_right.add(self.__label_result_count)
        layout_right.add(widgets.AbstractScrollArea(self.__table_cards))
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(layout_left, layout_right))
        self.set_layout(layout)

        # Connect signals
        self.__box_count.text_edited.connect(self.__on_query_edited)
        self.__box_score.text_edited.connect(self.__on_query_edited)
        self.__combo_proficiency.index_changed.connect(self.__on_query_edited)
        self.__combo_card_type.index_changed.connect(self.__on_query_edited)
        self.__combo_side.index_changed.connect(self.__on_query_edited)
        self.__combo_sort.index_changed.connect(self.__on_query_edited)
        self.__checkbox_random_forms.clicked.connect(self.__on_query_edited)
        self.__checkbox_only_once.clicked.connect(self.__on_query_edited)
        self.__button_begin.clicked.connect(self.__on_click_begin)

        self.__box_count.focus()
        self.__refresh_search_results()

    def __on_click_begin(self):
        """Begins the study state."""
        self.__refresh_search_results()
        if self.__cards and self.__study_params:
            study_set = StudySet(name="Study Query", cards=self.__cards)
            self.__application.push_study_state(study_set, params=self.__study_params)
                
    def __on_query_edited(self):
        """Called when the query widgets change."""
        self.__refresh_search_results()

    def __refresh_search_results(self):
        """Refresh the list of card search results."""

        # Define the query
        try:
            query = CardQuery()
            query.max_count = int(self.__box_count.get_text())
            query.max_proficiency = self.__combo_proficiency.get_index()
            query.max_score = float(self.__box_score.get_text())
            if self.__combo_card_type.get_index() > 0:
                query.card_type = getattr(WordType, self.__combo_card_type.get_text())
        except:
           cards = []
        else:
            # Query the cards
            temp = query.max_count
            query.max_count = None
            cards = list(self.__application.query_cards(query))
            query.max_count = temp

        # Sort the list
        cards = [(card, self.__application.study_database.get_card_study_data(card)) for card in cards]

        sort_method = self.__combo_sort.get_text()
        if sort_method == SortMethod.RANDOM:
            random.shuffle(cards)
            all_cards = list(cards)
            cards = []
            while all_cards and len(cards) < query.max_count:
                index = random.randrange(len(all_cards))
                elem = all_cards[index]
                del all_cards[index] 
                cards.append(elem)
        elif sort_method == SortMethod.LOWEST_SCORE:
            cards.sort(key=lambda x: x[1].get_history_score())
        elif sort_method == SortMethod.OLDEST:
            cards.sort(key=lambda x: x[1].get_last_encounter_time() or x[1].get_history_score())
        elif sort_method == SortMethod.NEWEST:
            cards.sort(key=lambda x: x[1].get_last_encounter_time() or x[1].get_history_score(), reverse=True)

        cards = cards[:query.max_count]

        # Define the study params
        params = StudyParams()
        params.random_side = self.__combo_side.get_index() == 0
        params.random_form = self.__checkbox_random_forms.is_checked()
        params.shown_side = (CardSide.English if self.__combo_side.get_index() == 1
                             else CardSide.Russian)
        self.__study_params = params
        
        # Popluate the table
        self.__table_cards.clear()
        for card, study_data in cards:
            row = self.__table_cards.add(card, enabled=True)
            color = Config.proficiency_level_colors[study_data.get_proficiency_level()]
            row.set_color(color)
        cards = [card for cards, _ in cards]

        self.__cards = cards
        self.__button_begin.set_enabled(len(cards) > 0 and self.__study_params)
        self.__label_result_count.set_text("{} Results".format(len(self.__cards)))
