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
from study_tool.russian.types import Aspect
from study_tool.russian.types import Gender
from study_tool.card import Card
from study_tool.card import get_card_key
from study_tool.card import get_card_english_key
from study_tool.card import get_card_russian_key
from study_tool.card import get_card_word_name
from study_tool.card_attributes import CardAttributes
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetType
from study_tool.entities.menu import Menu
from study_tool.gui.card_search_widget import CardSearchWidget
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from study_tool.russian.word import Word
from study_tool.russian.word import AccentedText
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from cmg.application import Application
from cmg.input import Keys
from cmg import widgets
from study_tool import card
from study_tool.config import Config


class CardRussianTextEdit(widgets.TextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attribute_font = cmg.Font(22)
        self.__attributes = set()
        self.__word = None
       
    def set_attributes(self, card_attributes):
        self.__attributes = set(card_attributes)
       
    def set_word(self, word):
        self.__word = word

    def on_draw(self, g):
        # Draw the text box
        widgets.TextEdit.on_draw(self, g)
        
        # Draw the attributes on the right
        rect = self.get_rect()
        padding = 2
        spacing = 2
        y_margin = 3
        x = rect.right - spacing
        y = rect.top
        height = rect.height
        
        # Draw the marker indicating word source
        w = height - (2 * y_margin)
        x -= w
        if self.__word:
            g.fill_rect(x, y + y_margin, w, w, color=Colors.GREEN)
        x -= spacing

        for attribute in self.__attributes:
            text = card_attributes.ATTRIBUTE_SHORT_DISPLAY_NAMES.get(
                attribute, attribute.value)
            width, _ = self.__attribute_font.measure(text)
            width += 2 * padding
            x -= width

            # Determine colors
            text_color = Colors.WHITE
            background_color = Colors.BLACK
            if attribute in card_attributes.ATTRIBUTE_COLORS:
                background_color = card_attributes.ATTRIBUTE_COLORS[attribute]
            
            # Draw the background box
            g.fill_rect(x, y + y_margin, width, height - (2 * y_margin),
                        color=background_color)

            # Draw the text in the box
            g.draw_accented_text(x + (width // 2),
                                 y + (rect.height // 2),
                                 text=text,
                                 font=self.__attribute_font,
                                 color=text_color,
                                 align=cmg.Align.Centered)
            x -= spacing


class CardRow(widgets.Widget):

    def __init__(self, card, card_set, card_database):
        super().__init__()
        self.card = card
        self.card_database = card_database
        self.modified = Event()
        self.russian_modified = Event(AccentedText)
        self.english_modified = Event(AccentedText)
        self.__card_set = card_set
        self.__is_new_card = True
        self.__card_match = None
        self.__word = None
        
        # Create widgets
        self.button_edit = widgets.Button("E")
        self.button_delete = widgets.Button("X")
        self.box_type = widgets.TextEdit("")
        self.box_type.set_minimum_width(90)
        self.box_russian = CardRussianTextEdit("")
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
        self.box_russian.focus_lost.connect(self.download_word_info)

        self.set_card(card)

    def get_column(self, column: int):
        if column == 0:
            return self.box_type
        if column == 1:
            return self.box_russian
        if column == 2:
            return self.box_english
        raise KeyError(column)

    def set_card(self, card: Card):
        """Sets the card to edit."""
        self.russian_modified.block(True)
        self.english_modified.block(True)
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
        self.russian_modified.block(False)
        self.english_modified.block(False)

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

    def is_incomplete(self) -> bool:
        return (not self.box_type.get_text() or
                not self.box_russian.get_text() or
                not self.box_english.get_text())

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

    def predict_word_type(self, russian: AccentedText):
        russian = AccentedText(russian).text.lower()

        word_type_endings = [
            (WordType.Adjective, ["ый", "ий", "ой"]),
            (WordType.Verb, ["ить", "ать", "еть", "ять", "уть", "ться", "сти", "стись"]),
            (WordType.Noun, ["ство", "ие", "ость", "а", "к", "ц", "г", "з"]),
            (WordType.Adverb, ["о"]),
        ]

        for word_type, endings in word_type_endings:
            for ending in endings:
                if russian.endswith(ending):
                    return word_type
        if " " in russian:
            return WordType.Phrase
        return None
    
    def auto_set_word_type(self) -> WordType:
        """
        Auto generates the word type based on the russian word ending.
        """
        word_type = self.predict_word_type(self.get_russian())
        if word_type is not None:
            self.box_type.set_text(
                get_word_type_short_name(word_type))
        return word_type

    def __auto_complete(self):
        if self.__card_match:
            self.set_card(self.__card_match)

    def __on_russian_changed(self):
        # Convert 'ээ' to an accent mark (for when typing in russian mode)
        russian = self.get_russian()
        if "ээ" in repr(russian).lower():
            russian = re.sub("ээ", "'", repr(russian), flags=re.IGNORECASE)
            self.box_russian.set_text(russian)
        self.russian_modified.emit(self.get_russian())
        self.__on_modified()

    def __on_english_changed(self):
        self.english_modified.emit(self.get_english())
        self.__on_modified()

    def __on_type_changed(self):
        self.__on_modified()

    def __on_modified(self):
        """Called when anything is modified."""
        empty = self.is_empty()
        valid = self.is_valid()
        modified = self.is_modified()
        word_type = self.get_word_type()
        russian = self.get_russian()
        english = self.get_english()
        new_in_database = not Config.app.card_database.has_card(self.card)
        new_in_set = not self.__card_set.has_card(self.card)

        # Look up the word and get important card attributes
        self.__word = None
        card_attributes = set()
        if word_type is not None and russian.text:
            word_name = get_card_word_name(russian)
            self.__word = Config.app.word_database.get_word(
                name=word_name.text, word_type=word_type)
            self.box_russian.set_word(self.__word)
            if isinstance(self.__word, Verb):
                if self.__word.get_aspect() == Aspect.Imperfective:
                    card_attributes.add(CardAttributes.Imperfective)
                elif self.__word.get_aspect() == Aspect.Perfective:
                    card_attributes.add(CardAttributes.Perfective)
            elif isinstance(self.__word, Noun):
                if self.__word.get_gender() == Gender.Masculine:
                    card_attributes.add(CardAttributes.Masculine)
                elif self.__word.get_gender() == Gender.Femanine:
                    card_attributes.add(CardAttributes.Femanine)
                elif self.__word.get_gender() == Gender.Neuter:
                    card_attributes.add(CardAttributes.Neuter)
            attrs = ", ".join(x.value for x in list(sorted(card_attributes)))
        else:
            self.box_russian.set_word(None)
        if not new_in_database:
            card_attributes = self.card.get_attributes()
        self.box_russian.set_attributes(card_attributes)
        
        # Check for duplicate key
        key = get_card_key(word_type, russian, english)
        existing_card = Config.app.card_database.get_card_by_key(key)
        if existing_card and existing_card != self.card:
            valid = False

        color = cmg.Theme.color_background
        color_default = cmg.Theme.color_background
        color_new = Config.color_edit_new
        color_invalid = Config.color_edit_invalid
        color_modified = Config.color_edit_modified
        
        if new_in_database and empty:
            color_word_type = color_default
            color_russian = color_default
            color_english = color_default
        else:
            if new_in_database:
                color = color_new
            else:
                if not valid:
                    color = color_invalid
                elif new_in_set:
                    color = color_new
            color_word_type = color
            color_russian = color
            color_english = color
       
            if word_type is None:
                color_word_type = color_invalid
            elif not new_in_database and word_type != self.card.get_word_type():
                color_word_type = color_modified
            if not russian.text:
                color_russian = color_invalid
            elif not new_in_database and repr(russian) != repr(self.card.get_russian()):
                color_russian = color_modified
            if not english.text:
                color_english = color_invalid
            elif not new_in_database and repr(english) != repr(self.card.get_english()):
                color_english = color_modified
        
            # Check for duplicate english/russian keys
            ru_key = get_card_russian_key(word_type, russian)
            en_key = get_card_english_key(
                word_type, english, card_attributes=card_attributes)
            existing_card = Config.app.card_database.get_card_by_russian_key(ru_key)
            if existing_card and existing_card != self.card:
                color_russian = color_invalid
            existing_card = Config.app.card_database.get_card_by_english_key(en_key)
            if existing_card and existing_card != self.card:
                color_english = color_invalid

        self.box_type.set_background_color(color_word_type)
        self.box_russian.set_background_color(color_russian)
        self.box_english.set_background_color(color_english)
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

    def download_word_info(self):
        if self.__word:
            return
        russian = self.get_russian().text.lower()
        if not russian:
            return
        word_type = self.get_word_type()
        if word_type is None:
            word_type = self.predict_word_type(russian)
        if word_type is None:
            return

        # Check if the word already exists
        word = Config.app.word_database.get_word(
            word_type=word_type, name=russian)
        if word is not None:
            text = get_word_type_short_name(word.get_word_type())
            self.box_type.set_text(text)
            self.__on_modified()
            return

        # Else, download the word
        def callback(word):
            if word:
                Config.app.word_database.add_word(word, replace=True)
                text = get_word_type_short_name(word.get_word_type())
                self.box_type.set_text(text)
                self.__on_modified()

        Config.app.cooljugator_thread.download_word_info(
            word_type=word_type, name=russian, callback=callback)


class CardSetEditWidget(widgets.Widget):
    """
    Widget to edit card sets.
    """

    def __init__(self, card_set: CardSet, application):
        super().__init__()
        self.set_window_title("Edit Card Set")
        if not card_set:
            card_set = CardSet()
        self.__card_set = card_set
        self.__application = application
        self.__card_database = self.__application.card_database
        self.rows = []

        # Create widgets
        self.__box_name = widgets.TextEdit()
        self.__combo_type = widgets.ComboBox(options=CardSetType)
        self.__button_add_card = widgets.Button("Add New Card")
        self.__button_save = widgets.Button("Save")
        self.__button_done = widgets.Button("Done")
        self.__button_convert = widgets.Button("Assimilate to YAML")
        self.__label_card_count = widgets.Label("Cards [{}]:".format(0))
        self.__label_path = widgets.Label("")
        self.__card_search_widget = CardSearchWidget(
            visible_func=lambda card: card not in self.get_cards())
        
        self.table = widgets.Widget()
        self.__layout_card_list = widgets.VBoxLayout()
        self.table.set_layout(self.__layout_card_list)

        # Create layouts
        left_layout = widgets.VBoxLayout()
        hbox = widgets.HBoxLayout()
        hbox.add(widgets.Label("Name:"))#), stretch=0)
        hbox.add(self.__combo_type)#, stretch=1)
        left_layout.add(hbox)
        left_layout.add(widgets.HBoxLayout(widgets.Label("Type:"), self.__combo_type))
        left_layout.add(widgets.HBoxLayout(widgets.Label("Path:"), self.__label_path))
        #left_layout.add(self.__button_convert)
        left_layout.add(widgets.HBoxLayout(self.__label_card_count, self.__button_add_card))
        left_layout.add(widgets.AbstractScrollArea(self.table))
        left_layout.add(widgets.HBoxLayout(self.__button_done, self.__button_save))
        layout = widgets.HBoxLayout()
        layout.add(left_layout, stretch=3)
        layout.add(self.__card_search_widget, stretch=1)
        self.set_layout(layout)
        
        self.select_card_set(card_set)

        # Connect signals
        self.__button_done.clicked.connect(self.__on_click_done)
        self.__button_save.clicked.connect(self.__on_click_save)
        self.__button_add_card.clicked.connect(self.__on_click_add_new_card)
        self.__button_convert.clicked.connect(self.__on_click_convert)
        self.__box_name.text_edited.connect(self.__on_modified)
        self.__card_search_widget.card_clicked.connect(self.__on_click_searched_card)
        self.add_key_shortcut("Ctrl+S", self.__on_click_save)

    def get_cards(self) -> list:
        cards = [row.card for row in self.rows if not row.is_null_card()]
        return cards

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

    def add_empty_row(self) -> CardRow:
        return self.add_card(Card(), fill_empty_row=False)

    def add_card(self, card: Card, fill_empty_row=True, row=None) -> CardRow:
        if row is not None:
            # Use the specifid row
            row.set_card(card)
        elif fill_empty_row and self.rows and self.rows[-1].is_empty():
            # Re-use the last empty row
            row = self.rows[-1]
            row.set_card(card)
        else:
            # Create a new row
            row = CardRow(card=card, card_set=self.__card_set, card_database=self.__card_database)
            row.box_type.return_pressed.connect(lambda: self.next_row(row, 0))
            row.box_russian.return_pressed.connect(lambda: self.next_row(row, 1))
            row.box_english.return_pressed.connect(lambda: self.next_row(row, 2))
            row.button_delete.clicked.connect(lambda: self.remove_row(row))
            row.button_edit.clicked.connect(lambda: self.__on_click_edit_card(card))
            row.modified.connect(self.__on_modified)
            row.english_modified.connect(lambda text: self.__card_search_widget.set_search_text(text))
            row.russian_modified.connect(lambda text: self.__card_search_widget.set_search_text(text))
            row.box_russian.add_key_shortcut("Ctrl+Space", lambda: self.__auto_complete(row, 1))
            row.box_english.add_key_shortcut("Ctrl+Space", lambda: self.__auto_complete(row, 2))
            self.rows.append(row)
            self.__layout_card_list.add(row)

        self.__on_modified()
        return row

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
                card_set_type=self.__combo_type.get_option(),
                cards=cards)

            self.select_card_set(self.__card_set)

            # Save any changes
            self.__application.save_all_changes()
            Config.app.word_database.save()

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
        self.__combo_type.set_option(self.__card_set.get_card_set_type())
        
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
        row = self.add_empty_row()
        row.box_russian.focus()

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

    def __auto_complete(self, row, column: int):
        search_text = self.__card_search_widget.get_search_text()
        card = self.__card_search_widget.get_first_result()
        if card:
            self.__card_search_widget.remove_from_results(card)
            row.set_card(card)
            next_row = self.add_empty_row()
            box = next_row.get_column(column)
            box.focus()
        return card

    def __on_click_searched_card(self, card: Card):
        self.__card_search_widget.remove_from_results(card)
        row = None
        if self.rows and self.rows[-1].is_incomplete():
            row = self.rows[-1]
        self.add_card(card, row=row)
        row = self.add_empty_row()
        row.box_russian.focus()
        
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
