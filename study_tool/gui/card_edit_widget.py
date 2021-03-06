from enum import IntEnum
import os
import pygame
import random
import re
import time
from cmg import widgets
from cmg import color
from cmg import math
from cmg.input import Keys
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool import card
from study_tool import card_attributes
from study_tool.config import Config
from study_tool.russian.types import WordType, get_word_type_short_name
from study_tool.russian.verb import Verb
from study_tool.russian.word import Word, split_words, AccentedText
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.gui.card_search_widget import CardSearchWidget
from study_tool.card_database import CardDatabase


class WordInfoWidget(widgets.GroupBox):
    def __init__(self):
        super().__init__("Word Info")
        self.__word = None

        self.__label_definition = widgets.Label("")
        self.__label_other_meanings = widgets.Label("")
        self.__label_counterparts = widgets.Label("")

        layout = widgets.VBoxLayout()
        layout.add(self.__label_definition)
        layout.add(self.__label_other_meanings)
        layout.add(widgets.HBoxLayout(widgets.Label("Counterparts:"), self.__label_counterparts))
        self.set_layout(layout)

    def set_word(self, word):
        self.__word = word
        self.__label_definition.set_text("")
        self.__label_other_meanings.set_text("")
        self.__label_counterparts.set_text("")

        if word is not None:
            self.__label_definition.set_text(
                "{} - {}".format(repr(self.__word.get_name()),
                                 repr(self.__word.get_meaning())))

            if isinstance(self.__word, Verb):
                self.__label_definition.set_text(
                    "{} - {}".format(repr(self.__word.get_name()),
                                     repr(self.__word.get_translation())))
                self.__label_other_meanings.set_text(
                    repr(self.__word.get_info()))
                self.__label_counterparts.set_text(
                    ", ".join(repr(x) for x in self.__word.get_counterparts()))


class CardRow(widgets.Widget):
    def __init__(self, card: Card):
        super().__init__()
        self.card = card

        self.edit_card_type = widgets.Label(
            get_word_type_short_name(card.get_word_type()) + ".")
        self.edit_russian = widgets.Label(repr(card.get_russian()))
        self.edit_english = widgets.Label(repr(card.get_english()))
        self.button_select = widgets.Button("Select")

        self.button_select.set_enabled(
            self.card.get_fixed_card_set() is None)

        layout = widgets.HBoxLayout()
        layout.add_widget(self.edit_card_type)
        layout.add_widget(self.edit_russian)
        layout.add_widget(self.edit_english)
        layout.add_widget(self.button_select)
        self.set_layout(layout)


class CardEditWidget(widgets.Widget):

    def __init__(self, card: Card, application,
                 allow_card_change=True, close_on_apply=True):
        super().__init__()
        if not card:
            card = Card()
        self.__card = card
        self.__application = application
        self.__card_database = application.card_database
        self.__allow_card_change = allow_card_change
        self.__close_on_apply = close_on_apply

        self.__attribute_to_widget_dict = {}
        self.__widget_to_attribute_dict = {}
        self.__related_card_to_widget_dict = {}
        self.__widget_to_related_card_dict = {}

        self.updated = Event(Card)

        # Create widgets
        self.__word_info_widget = WordInfoWidget()
        self.__box_card_type = widgets.TextEdit()
        self.__box_english = widgets.TextEdit()
        self.__box_russian = widgets.TextEdit()
        self.__box_add_attribute = widgets.TextEdit()
        self.__box_add_related_word = widgets.TextEdit()
        self.__layout_card_sets = widgets.VBoxLayout()
        self.__label_word_info = widgets.Label("None")
        self.__button_add_attribute = widgets.Button("Add Attribute")
        self.__button_add_related_word = widgets.Button("Add")
        self.__layout_attributes = widgets.VBoxLayout()
        self.__layout_related_cards = widgets.VBoxLayout()
        self.__button_apply = widgets.Button("Apply")
        self.__button_delete = widgets.Button("Delete")
        self.__button_cancel = widgets.Button("Cancel")
        self.__button_new_card = widgets.Button("Create New Card")
        self.__card_search_widget = CardSearchWidget(
            visible_func=lambda card: card is not self.__card)

        self.__box_card_type.set_autocomplete_source([x.name for x in WordType])
        self.__box_add_attribute.set_autocomplete_source([x.value for x in CardAttributes])
        self.__box_add_related_word.set_autocomplete_source(
            [x.get_russian().text for x in self.__card_database.iter_cards()])

        # Create layouts
        layout_identification = widgets.GridLayout()
        layout_identification.set_column_stretch(0, 1)
        layout_identification.set_column_stretch(1, 4)
        layout_identification.add(widgets.Label("Russian:"), 0, 0)
        layout_identification.add(widgets.Label("English:"), 1, 0)
        layout_identification.add(widgets.Label("Type:"), 2, 0)
        layout_identification.add(self.__box_russian, 0, 1)
        layout_identification.add(self.__box_english, 1, 1)
        layout_identification.add(self.__box_card_type, 2, 1)
        layout_related_cards = widgets.VBoxLayout()
        layout_related_cards.add(widgets.HBoxLayout(self.__box_add_related_word, self.__button_add_related_word))
        layout_related_cards.add(self.__layout_related_cards)
        layout_attributes = widgets.VBoxLayout()
        layout_attributes.add(widgets.HBoxLayout(self.__box_add_attribute, self.__button_add_attribute))
        layout_attributes.add(self.__layout_attributes)
        layout = widgets.VBoxLayout()
        layout.add(widgets.GroupBox("Card Text", layout_identification))
        layout.add(widgets.GroupBox("Attributes", layout_attributes))
        layout.add(widgets.GroupBox("Related Cards", layout_related_cards))
        layout.add(widgets.GroupBox("Card Sets", self.__layout_card_sets))
        layout.add(self.__word_info_widget)
        layout.add(widgets.HBoxLayout(self.__button_apply,
                                      self.__button_delete,
                                      self.__button_cancel))
        self.set_layout(widgets.HBoxLayout(
            layout,
            widgets.VBoxLayout(self.__button_new_card,
                                self.__card_search_widget)))

        # Initialize with card data
        self.select_card(card)
        self.__card_search_widget.set_search_text(self.get_russian().text)
        
        # Connect signals
        self.__box_russian.return_pressed.connect(self.__box_english.focus)
        self.__box_english.return_pressed.connect(self.__box_card_type.focus)
        self.__box_card_type.return_pressed.connect(self.__box_add_attribute.focus)
        self.__box_english.text_edited.connect(self.__on_english_changed)
        self.__box_russian.text_edited.connect(self.__on_russian_changed)
        self.__box_card_type.text_edited.connect(self.__on_card_type_changed)
        self.__box_add_attribute.return_pressed.connect(self.__on_click_add_attribute)
        self.__button_add_attribute.clicked.connect(self.__on_click_add_attribute)
        self.__box_add_related_word.return_pressed.connect(self.__on_click_add_related_card)
        self.__button_add_related_word.clicked.connect(self.__on_click_add_related_card)
        self.__button_apply.clicked.connect(self.apply)
        self.add_key_shortcut("Ctrl+S", self.apply)
        self.__button_delete.clicked.connect(self.delete_card)
        self.__button_cancel.clicked.connect(self.__on_click_cancel)
        self.__button_new_card.clicked.connect(
            lambda: (self.select_card(None), self.__box_russian.focus()))
        self.__card_search_widget.card_clicked.connect(self.__on_click_searched_card)
        
        self.__box_russian.focus()
        
    def get_card(self) -> Card:
        return self.__card

    def get_key(self) -> tuple:
        card_type = self.get_card_type()
        russian = self.get_russian()
        english = self.get_english()
        return (card_type, russian.text, english.text)

    def get_russian(self) -> AccentedText:
        return AccentedText(self.__box_russian.get_text())

    def get_english(self) -> AccentedText:
        return AccentedText(self.__box_english.get_text())
    
    def get_card_type(self) -> WordType:
        return getattr(WordType, self.__box_card_type.get_text(), None)

    def get_attributes(self) -> list:
        return tuple(sorted(
            [k for k, _ in self.__attribute_to_widget_dict.items()],
            key=lambda x: x.name))

    def get_related_cards(self) -> list:
        return tuple(sorted(
            [k for k, _ in self.__related_card_to_widget_dict.items()],
            key=lambda x: x.get_key()))

    def get_card_attributes(self) -> list:
        return tuple(sorted(self.__card.get_attributes(),
                            key=lambda x: x.name))
    
    def select_card(self, card: Card):
        """Sets the card that is being edited."""
        # Initialize with card data
        if card is None:
            card = Card()
        self.__card = card
        if self.__card.get_word_type() is not None:
            self.__box_card_type.set_text(self.__card.get_word_type().name)
        else:
            self.__box_card_type.set_text("")
        self.__label_word_info.set_text("")
        self.__box_russian.set_text(repr(self.__card.get_russian()))
        self.__box_english.set_text(repr(self.__card.get_english()))
        self.clear_attributes()
        for attribute in self.__card.get_attributes():
            self.add_attribute(attribute)
        self.clear_related_cards()
        for related_card in self.__card.get_related_cards():
            self.add_related_card(related_card)

        card_sets = []
        for card_set in self.__application.iter_card_sets():
            if card_set.has_card(self.__card):
                card_sets.append(card_set)
        self.__layout_card_sets.clear()
        for card_set in card_sets:
            self.__layout_card_sets.add(widgets.Label(card_set.get_name().text))

        if self.__card_database.has_card(self.__card):
            self.__button_apply.set_text("Update")
            self.__button_delete.set_enabled(True)
        else:
            self.__button_apply.set_text("Create")
            self.__button_delete.set_enabled(False)

        self.__refresh_word_data()

    def apply(self):
        """Apply card changes or create a new card."""
        try:
            assert self.__is_valid_key()

            created = not self.__card_database.has_card(self.__card)
        
            # Create the card representing the widget state
            new_card = Card(copy=self.__card,
                            russian=self.get_russian(),
                            english=self.get_english(),
                            word_type=self.get_card_type(),
                            attributes=self.get_attributes(),
                            related_cards=self.get_related_cards(),
                            examples=self.__card.get_examples())

            if created:
                # Create a new card
                self.__card = new_card
                self.__card_database.add_card(self.__card)
                self.__application.save_card_data()
                self.select_card(self.__card)
            else:
                # Apply the card updates
                self.__card_database.update_card(
                    original=self.__card, modified=new_card)

                # Save changes
                self.__application.save_all_changes()

            self.updated.emit(self.__card)
            Config.logger.info("Success!")
            if self.__close_on_apply:
                self.close()
            elif created:
                self.select_card(None)
                self.__box_russian.focus()
        except Exception:
            traceback.print_exc()
            return

    def delete_card(self):
        return
        assert self.__card_database.has_card(self.__card)
        self.__card_database.delete_card(self.__card)
        self.__card_database.save_all_changes()
        self.select_card(None)

    def clear_attributes(self):
        self.__attribute_to_widget_dict = {}
        self.__widget_to_attribute_dict = {}
        self.__layout_attributes.clear()
        self.__on_attributes_changed()

    def clear_related_cards(self):
        self.__related_card_to_widget_dict = {}
        self.__widget_to_related_card_dict = {}
        self.__layout_related_cards.clear()

    def add_attribute(self, attribute: CardAttributes):
        name = card_attributes.get_card_attribute_display_name(attribute)
        widget = widgets.Button(name)
        widget.clicked.connect(lambda: self.remove_attribute(attribute))
        self.__layout_attributes.add(widget)
        self.__attribute_to_widget_dict[attribute] = widget
        self.__widget_to_attribute_dict[widget] = attribute
        self.__on_attributes_changed()

    def remove_attribute(self, attribute: CardAttributes):
        widget = self.__attribute_to_widget_dict[attribute]
        self.__layout_attributes.remove(widget)
        del self.__attribute_to_widget_dict[attribute]
        del self.__widget_to_attribute_dict[widget]
        self.__on_attributes_changed()

    def add_related_card(self, related_card: Card):
        name = related_card.get_russian().text
        widget = widgets.Button(name)
        widget.clicked.connect(lambda: self.remove_related_card(related_card))
        self.__layout_related_cards.add(widget)
        self.__related_card_to_widget_dict[related_card] = widget
        self.__widget_to_related_card_dict[widget] = related_card

    def remove_related_card(self, related_card: Card):
        widget = self.__related_card_to_widget_dict[related_card]
        self.__layout_related_cards.remove(widget)
        del self.__related_card_to_widget_dict[related_card]
        del self.__widget_to_related_card_dict[widget]

    def __refresh_word_data(self):
        """Look up or download word information for the card."""
        word_type = self.get_card_type()
        russian = self.get_russian()
        word_name = russian
        word_tokens = list(split_words(russian.text))
        if len(word_tokens) > 0:
            word_name = AccentedText(word_tokens[0][0])
        
        # Look up the word
        word = None
        if word_type is not None:
            word = self.__application.word_database.get_word(
                name=word_name, word_type=word_type)

        self.__word_info_widget.set_word(word)

    def __on_click_cancel(self):
        if self.__close_on_apply:
            self.close()
        else:
            self.select_card(self.__card)

    def __on_click_add_attribute(self):
        text = self.__box_add_attribute.get_text()
        attribute = None
        try:
            attribute = CardAttributes(text)
        except:
            return
        if attribute is not None and attribute not in self.get_attributes():
            self.add_attribute(attribute)
            self.__box_add_attribute.set_text("")
            self.__box_add_attribute.focus()
            self.__box_add_attribute.set_text("")

    def __on_click_add_related_card(self):
        text = AccentedText(self.__box_add_related_word.get_text())
        related_card = self.__card_database.find_card(russian=text)
        if related_card and related_card not in self.get_related_cards():
            self.add_related_card(related_card)
            self.__box_add_related_word.set_text("")
            self.__box_add_related_word.focus()
            self.__box_add_related_word.set_text("")

    def __on_english_changed(self):
        self.__on_key_changed()
        self.__card_search_widget.set_search_text(self.get_english().text)

    def __on_russian_changed(self):
        # Convert 'ээ' to an accent mark (for when typing in russian mode)
        russian = self.get_russian()
        if "ээ" in repr(russian).lower():
            russian = re.sub("ээ", "'", repr(russian), flags=re.IGNORECASE)
            self.__box_russian.set_text(russian)
        self.__on_key_changed()
        self.__refresh_word_data()
        self.__card_search_widget.set_search_text(self.get_russian().text)

    def __on_card_type_changed(self):
        self.__on_key_changed()
        self.__refresh_word_data()

    def __on_key_changed(self):
        valid = self.__is_valid_key()
        self.__button_apply.set_enabled(valid)
    
    def __on_attributes_changed(self):
        pass
    
    def __on_click_searched_card(self, card: Card):
        self.__card_search_widget.refresh()
        self.select_card(card)

    def __is_valid_key(self) -> bool:
        card_type = self.get_card_type()
        russian = self.get_russian()
        english = self.get_english()
        return card_type is not None and english and russian
