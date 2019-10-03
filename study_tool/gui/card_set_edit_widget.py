from enum import IntEnum
import os
import pygame
import random
import re
import time
import traceback
from cmg import color
from cmg.color import Color, Colors
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from cmg.event import Event
from study_tool import card_attributes
from study_tool.russian.types import WordType, get_word_type_short_name, parse_short_word_type
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.card_set import CardSet
from study_tool.entities.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from cmg.application import Application
from cmg.input import Keys
from cmg import widgets
from study_tool import card
from study_tool.config import Config

class CardRow(widgets.Widget):

    def __init__(self, card, card_set, card_database):
        super().__init__()
        self.card = card
        self.card_database = card_database
        self.modified = Event()
        self.__card_set = card_set
        self.__is_new_card = True
        self.__card_match = None
        
        # Create widgets
        self.button_edit = widgets.Button("E")
        self.button_delete = widgets.Button("X")
        self.box_type = widgets.TextEdit("")
        self.box_type.set_minimum_width(90)
        self.box_russian = widgets.TextEdit("")
        self.box_english = widgets.TextEdit("")

        word_types = [get_word_type_short_name(word_type)
                      for word_type in WordType]
        self.box_type.set_autocomplete_source(word_types)

        # Create layout
        layout = widgets.HBoxLayout()
        layout.add(self.box_type, stretch=0)
        layout.add(self.box_russian, stretch=1)
        layout.add(self.box_english, stretch=1)
        layout.add(self.button_edit, stretch=0)
        layout.add(self.button_delete, stretch=0)
        self.set_layout(layout)

        # Connect signals
        self.box_russian.text_edited.connect(self.__on_russian_changed)
        self.box_english.text_edited.connect(self.__on_english_changed)
        self.box_type.text_edited.connect(self.__on_type_changed)
        self.box_russian.return_pressed.connect(self.__auto_complete)

        self.set_card(card)

    def set_card(self, card: Card):
        self.card = card
        self.__is_new_card = not self.card_database.has_card(card)
        fixed = self.card.get_fixed_card_set() is not None

        word_type = card.get_word_type()
        if word_type is not None:
            self.box_type.set_text(get_word_type_short_name(card.get_word_type()))
        else:
            self.box_type.set_text("")
        self.box_russian.set_text(repr(self.card.get_russian()))
        self.box_english.set_text(repr(self.card.get_english()))
        self.button_edit.set_enabled(not fixed)
        self.button_delete.set_enabled(not fixed)
        self.__on_modified()

    def apply(self):
        """Applies changes to the card."""
        if self.is_null_card():
            return
        assert self.is_valid()

        created = not self.card_database.has_card(self.card)
        new_card = Card(copy=self.card,
                        russian=self.get_russian(),
                        english=self.get_english(),
                        word_type=self.get_word_type())
        if created:
            Config.logger.info("Creating new card: " + repr(new_card))
            self.card = new_card
            self.card_database.add_card(self.card)
        else:
            self.card_database.update_card(
                original=self.card, modified=new_card)
        self.set_card(self.card)
    
    def auto_set_word_type(self) -> WordType:
        russian = self.get_russian().text.lower()
        
        word_type_endings_dict = {
            WordType.Adjective: ["ый", "ий", "ой"],
            WordType.Verb: ["ить", "ать", "еть", "ять", "уть", "ться", "сти", "стись"],
            WordType.Noun: ["ие", "ость", "а"],
            WordType.Adverb: ["о"],
        }

        for word_type, endings in word_type_endings_dict.items():
            for ending in endings:
                if russian.endswith(ending):
                    self.box_type.set_text(
                        get_word_type_short_name(word_type))
                    return word_type
        if " " in russian:
            return WordType.Phrase
        return None

    def get_word_type(self) -> WordType:
        return parse_short_word_type(self.box_type.get_text())

    def get_russian(self) -> AccentedText:
        return AccentedText(self.box_russian.get_text())
    
    def get_english(self) -> AccentedText:
        return AccentedText(self.box_english.get_text())

    def is_null_card(self) -> bool:
        return self.__is_new_card and self.is_empty()

    def is_valid(self) -> bool:
        card_type = self.get_word_type()
        russian = self.get_russian()
        english = self.get_english()
        return card_type is not None and english.text and russian.text

    def is_new_card(self) -> bool:
        return False

    def is_new_in_set(self) -> bool:
        return not self.__card_set.has_card(self.card)

    def is_empty(self) -> bool:
        return (not self.box_type.get_text() and
                not self.box_russian.get_text() and
                not self.box_english.get_text())

    def is_modified(self):
        card_type = self.get_word_type()
        russian = self.get_russian()
        english = self.get_english()
        return (card_type != self.card.get_word_type() or
                repr(russian) != repr(self.card.get_russian()) or
                repr(english) != repr(self.card.get_english()))

    def __auto_complete(self):
        if self.__card_match:
            self.set_card(self.__card_match)
    
    def __on_russian_changed(self):
        # Convert 'ээ' to an accent mark (for when typing in russian mode)
        russian = self.get_russian()
        if "ээ" in repr(russian).lower():
            russian = re.sub("ээ", "'", repr(russian), flags=re.IGNORECASE)
            self.box_russian.set_text(russian)
        self.__on_modified()

    def __on_english_changed(self):
        self.__on_modified()

    def __on_type_changed(self):
        self.__on_modified()

    def __on_modified(self):
        empty = self.is_empty()
        bg_color = Colors.WHITE
        if not self.__card_set.has_card(self.card):
            if not empty:
                if self.is_valid():
                    bg_color = Color(200, 255, 200)
                else:
                    bg_color = Color(255, 200, 200)
        else:
            if not self.is_valid():
                bg_color = Color(255, 200, 200)
            elif self.is_modified():
                bg_color = Color(255, 255, 200)
        self.box_type.set_background_color(bg_color)
        self.box_russian.set_background_color(bg_color)
        self.box_english.set_background_color(bg_color)
        self.modified.emit()
        self.__refresh_matches()
        
    def __refresh_matches(self):
        word_type = self.get_word_type()
        russian = self.get_russian()
        english = self.get_english()

        match = None
        if not repr(english):
            for index, card in enumerate(self.card_database.iter_cards()):
                if self.matches(card, card_type=word_type, russian=russian):
                    match = card
                    break
        
        if match is not None:
            self.box_english.set_background_text(repr(match.get_english()))
        else:
            self.box_english.set_background_text(None)
        self.__card_match = match

    def matches(self, card, card_type, russian, english=None):
        russian = russian.text.lower() if russian else None
        english = english.text.lower() if english else None
        if card_type is not None and card_type != card.get_word_type():
            return False
        if russian and russian != card.get_russian().text.lower():
            return False
        if english and english != card.get_english().text.lower():
            return False
        return card_type is not None or russian or english


class CardSetEditWidget(widgets.Widget):
    def __init__(self, card_set: CardSet, application):
        super().__init__()
        if not card_set:
            card_set = CardSet()
        self.__card_set = card_set
        self.__application = application
        self.__card_database = self.__application.card_database
        self.rows = []

        # Create widgets
        self.__box_name = widgets.TextEdit()
        self.__button_add_card = widgets.Button("Add New Card")
        self.__button_save = widgets.Button("Save")
        self.__button_done = widgets.Button("Done")
        self.__button_convert = widgets.Button("Assimilate to YAML")
        self.__label_card_count = widgets.Label("Cards [{}]:".format(0))
        self.__label_path = widgets.Label("")
        
        self.table = widgets.Widget()
        self.__layout_card_list = widgets.VBoxLayout()
        self.table.set_layout(self.__layout_card_list)

        # Create layouts
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(widgets.Label("Name:"), self.__box_name))
        layout.add(widgets.HBoxLayout(widgets.Label("Path:"), self.__label_path))
        layout.add(self.__button_convert)
        layout.add(widgets.HBoxLayout(self.__label_card_count, self.__button_add_card))
        layout.add(widgets.AbstractScrollArea(self.table))
        layout.add(widgets.HBoxLayout(self.__button_done, self.__button_save))
        self.set_layout(layout)
        
        self.select_card_set(card_set)

        # Connect signals
        self.__button_done.clicked.connect(self.__on_click_done)
        self.__button_save.clicked.connect(self.__on_click_save)
        self.__button_add_card.clicked.connect(self.__on_click_add_new_card)
        self.__button_convert.clicked.connect(self.__on_click_convert)
        self.__box_name.text_edited.connect(self.__on_modified)
        
        self.__box_name.focus()

    def is_modified(self) -> bool:
        """Returns True if anything is modified."""
        name = AccentedText(self.__box_name.get_text())
        if repr(name) != repr(self.__card_set.get_name()):
            return True

        new_cards = [row.card for row in self.rows if not row.is_null_card()]
        old_cards = self.__card_set.get_cards()
        if (len(old_cards) != len(new_cards) or
            any(a is not b for a, b in zip(old_cards, new_cards))):
                return True

        for row in self.rows:
            if not row.is_null_card() and row.is_modified():
                return True

        return False

    def add_empty_row(self):
        self.add_card(Card(), fill_empty_row=False)

    def add_card(self, card: Card, fill_empty_row=True):
        # Find the last empty row
        if fill_empty_row and self.rows and self.rows[-1].is_empty():
            row = self.rows[-1]
            row.set_card(card)
        else:
            row = CardRow(card=card, card_set=self.__card_set, card_database=self.__card_database)
            self.rows.append(row)
            self.__layout_card_list.add(row)

        row.box_type.return_pressed.connect(lambda: self.next_row(row, 0))
        row.box_russian.return_pressed.connect(lambda: self.next_row(row, 1))
        row.box_english.return_pressed.connect(lambda: self.next_row(row, 2))
        row.button_delete.clicked.connect(lambda: self.remove_row(row))
        row.button_edit.clicked.connect(lambda: self.__on_click_edit_card(card))
        row.modified.connect(self.__on_modified)
        self.__on_modified()

    def remove_card(self, card: Card):
        index = [row.card for row in self.rows].index(card)
        self.remove_row(self.rows[index])
    
    def remove_row(self, row: CardRow):
        index = self.rows.index(row)
        row = self.rows[index]
        del self.rows[index]
        self.__layout_card_list.remove(row)
        if index == len(self.rows):
            self.add_empty_row()
        self.__on_modified()

    def next_row(self, row: CardRow, column: int):
        index = self.rows.index(row)
        if index + 1 >= len(self.rows):
            self.add_empty_row()
        next_row = self.rows[index + 1]
        if column == 0:
            box = next_row.box_type
            next_row.auto_set_word_type()
        elif column == 1:
            box = next_row.box_russian
        elif column == 2:
            box = next_row.box_english
        box.focus()

    def apply(self):
        """Save the card set to file."""
        try:
            # Apply card changes and create new cards
            for row in self.rows:
                row.apply()
            cards = [row.card for row in self.rows if not row.is_null_card()]

            # Update the card set
            name = AccentedText(self.__box_name.get_text())
            self.__card_database.update_card_set(
                card_set=self.__card_set,
                name=name,
                cards=cards)

            self.select_card_set(self.__card_set)

            # Save any changes
            self.__application.save_all_changes()

        except Exception:
            traceback.print_exc()
            return

    def select_card_set(self, card_set):
        self.__card_set = card_set

        self.__button_done.set_enabled(not self.__card_set.is_fixed_card_set())
        self.__button_add_card.set_enabled(not self.__card_set.is_fixed_card_set())
        self.__label_path.set_text(str(self.__card_set.get_file_path()))
        self.__label_card_count.set_text(
            "Cards [{}]:".format(self.__card_set.get_card_count()))
        self.__box_name.set_text(repr(self.__card_set.get_name()))
        
        self.__button_convert.set_text("Assimilate set to YAML")
        self.__button_convert.set_enabled(self.__card_set.is_fixed_card_set())
        if self.__card_set.is_fixed_card_set():
            old_file_path = self.__card_set.get_file_path()
            card_sets_in_file = self.__card_database.get_card_sets_from_path(old_file_path)
            if len(card_sets_in_file) > 1:
                self.__button_convert.set_text(
                    "Assimilate {} sets to YAML".format(len(card_sets_in_file)))

        self.rows = []
        self.__layout_card_list.clear()
        for card in self.__card_set.get_cards():
            self.add_card(card)
        self.add_empty_row()

    def __on_click_convert(self):
        self.__application.assimilate_card_set_to_yaml(self.__card_set)
        self.select_card_set(self.__card_set)

    def __on_click_add_new_card(self):
        widget = self.__application.push_card_edit_state(
            Card(), allow_card_change=True)
        widget.updated.connect(self.__on_card_updated)

    def __on_click_edit_card(self, card: Card):
        widget = self.__application.push_card_edit_state(
            card, allow_card_change=False)
        widget.updated.connect(self.__on_card_updated)
        
    def __on_click_done(self):
        self.apply()
        self.close()

    def __on_click_save(self):
        if self.is_modified():
            self.apply()

    def __on_card_updated(self, card: Card):
        """Called when a card in the set is updated."""
        if self.__has_card(card):
            row = self.__get_row_from_card(card)
            row.set_card(card)
        else:
            self.add_card(card, fill_empty_row=True)
            self.add_empty_row()
        self.__on_modified()

    def __on_modified(self):
        modified = self.is_modified()
        self.__button_save.set_enabled(modified)

    def __get_row_from_card(self, card: Card) -> int:
        index = [row.card for row in self.rows].index(card)
        return self.rows[index]

    def __has_card(self, card: Card) -> bool:
        return card in (row.card for row in self.rows)
