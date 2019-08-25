from enum import IntEnum
import os
import pygame
import random
import re
import time
from cmg import color
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool import card_attributes
from study_tool.russian.types import WordType, get_word_type_short_name
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.card_set import *
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from cmg.input import Keys
from cmg import widgets
from study_tool import card
from study_tool.config import Config


class CardRow(widgets.Widget):
    def __init__(self, card):
        super().__init__()
        self.card = card

        self.edit_card_type = widgets.Label(
            get_word_type_short_name(card.word_type) + ".")
        self.edit_russian = widgets.Label(repr(card.russian))
        self.edit_english = widgets.Label(repr(card.english))
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

    def __init__(self, card: Card, application):
        super().__init__()
        if not card:
            card = Card()
        self.__card = card
        self.__application = application
        self.__card_database = application.card_database

        self.__attribute_to_widget_dict = {}
        self.__widget_to_attribute_dict = {}

        self.updated = Event(Card)

        # Create widgets
        self.__box_card_type = widgets.TextEdit()
        self.__box_english = widgets.TextEdit()
        self.__box_russian = widgets.TextEdit()
        self.__box_add_attribute = widgets.TextEdit()
        self.__label_sets = widgets.Label("")
        self.__button_add_attribute = widgets.Button("Add Attribute")
        self.__layout_attributes = widgets.HBoxLayout()
        self.__button_apply = widgets.Button("Apply")
        self.__button_delete = widgets.Button("Delete")
        self.__button_cancel = widgets.Button("Cancel")
        self.__button_new_card = widgets.Button("Create New Card")
        
        self.__table = widgets.Widget()
        self.__layout_card_list = widgets.VBoxLayout()
        self.__table.set_layout(self.__layout_card_list)

        self.__box_card_type.set_autocomplete_source([x.name for x in WordType])
        self.__box_add_attribute.set_autocomplete_source([x.value for x in CardAttributes])

        # Create layouts
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(widgets.Label("Russian:"), self.__box_russian))
        layout.add(widgets.HBoxLayout(widgets.Label("English:"), self.__box_english))
        layout.add(widgets.HBoxLayout(widgets.Label("Type:"), self.__box_card_type))
        layout.add(widgets.HBoxLayout(widgets.Label("Attributes:"), self.__box_add_attribute, self.__button_add_attribute))
        layout.add(widgets.HBoxLayout(self.__layout_attributes))
        layout.add(self.__label_sets)
        layout.add(widgets.HBoxLayout(self.__button_apply,
                                      self.__button_delete,
                                      self.__button_cancel))
        self.set_layout(widgets.HBoxLayout(
            layout,
            widgets.VBoxLayout(self.__button_new_card,
                               widgets.AbstractScrollArea(self.__table))))
        
        # Initialize with card data
        self.select_card(card)
        
        # Connect signals
        self.__box_russian.return_pressed.connect(self.__box_english.focus)
        self.__box_english.return_pressed.connect(self.__box_card_type.focus)
        self.__box_card_type.return_pressed.connect(self.__box_add_attribute.focus)
        self.__box_add_attribute.return_pressed.connect(self.__on_click_add_attribute)
        self.__box_english.text_edited.connect(self.__on_english_changed)
        self.__box_russian.text_edited.connect(self.__on_russian_changed)
        self.__box_card_type.text_edited.connect(self.__on_card_type_changed)
        self.__button_add_attribute.clicked.connect(self.__on_click_add_attribute)
        self.__button_apply.clicked.connect(self.apply)
        self.__button_delete.clicked.connect(self.delete_card)
        self.__button_cancel.clicked.connect(self.close)
        self.__button_new_card.clicked.connect(
            lambda: (self.select_card(None), self.__box_russian.focus()))
        
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
        self.__box_russian.set_text(repr(self.__card.get_russian()))
        self.__box_english.set_text(repr(self.__card.get_english()))
        self.clear_attributes()
        for attribute in self.__card.get_attributes():
            self.add_attribute(attribute)

        card_sets = []
        for card_set in self.__application.iter_card_sets():
            if card_set.has_card(self.__card):
                card_sets.append(card_set)
        self.__label_sets.set_text(
            "Sets: " + ", ".join(x.get_name().text for x in card_sets))

        if self.__card_database.has_card(self.__card):
            self.__button_apply.set_text("Update")
            self.__button_delete.set_enabled(True)
        else:
            self.__button_apply.set_text("Create")
            self.__button_delete.set_enabled(False)

    def apply(self):
        """Apply card changes or create a new card."""
        assert self.__is_valid_key()

        if self.__card_database.has_card(self.__card):
            Config.logger.info("Applying card updates for: " + repr(self.__card))
        
        # Update card key values
        old_key = self.__card.get_key()
        self.__card.set_russian(self.get_russian())
        self.__card.set_english(self.get_english())
        self.__card.set_word_type(self.get_card_type())
        new_key = self.__card.get_key()

        # Update attributes
        old_attrs = self.get_card_attributes()
        new_attrs = self.get_attributes()
        if new_attrs != old_attrs:
            self.__card.clear_attributes()
            for attr in new_attrs:
                self.__card.add_attribute(attr)

        if not self.__card_database.has_card(self.__card):
            # Create new card
            self.__card_database.add_card(self.__card)
            self.__application.save_card_data()
            Config.logger.info("Created new card: " + repr(self.__card))
            self.select_card(self.__card)

        else:
            # Check for a key change
            if new_key != old_key:
                Config.logger.info("Applying key change: {} --> {}"
                                   .format(old_key, new_key))
            self.__card_database.apply_card_key_change(self.__card)

            # Save card database
            Config.logger.info("Saving card data")
            self.__application.save_card_data()

            # Save study data and relevant card sets if there is a key change
            if new_key != old_key:
                Config.logger.info("Saving study data")
                self.__application.save_study_data()
                for card_set in self.__application.iter_card_sets():
                    if card_set.has_card(self.__card):
                        Config.logger.info("Saving card set data for '{}'"
                                           .format(card_set.get_name()))
                        assert not card_set.is_fixed_card_set()
                        self.__application.save_card_set(card_set)

        self.updated.emit(self.__card)
        Config.logger.info("Success!")
        self.close()

    def delete_card(self):
        assert self.__card_database.has_card(self.__card)
        Config.logger.info("Deleting card: " + repr(self.__card))
        self.__card_database.remove_card(self.__card)
        
        # Remove card from card sets
        for card_set in self.__application.iter_card_sets():
            if card_set.has_card(self.__card):
                assert not card_set.is_fixed_card_set()
                Config.logger.info("Removing card from card set '{}'"
                                    .format(card_set.get_name()))
                card_set.remove_card(self.__card)
                self.__application.save_card_set(card_set)
        
        Config.logger.info("Saving study data")
        self.__application.save_study_data()
        Config.logger.info("Saving card data")
        self.__application.save_card_data()

        self.select_card(None)

    def clear_attributes(self):
        self.__attribute_to_widget_dict = {}
        self.__widget_to_attribute_dict = {}
        self.__layout_attributes.clear()
        self.__on_attributes_changed()

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

    def __on_english_changed(self):
        self.__on_key_changed()

    def __on_russian_changed(self):
        # Convert 'ээ' to an accent mark (for when typing in russian mode)
        russian = self.get_russian()
        if "ээ" in repr(russian).lower():
            russian = re.sub("ээ", "'", repr(russian), flags=re.IGNORECASE)
            self.__box_russian.set_text(russian)
        self.__on_key_changed()

    def __on_card_type_changed(self):
        self.__on_key_changed()

    def __on_key_changed(self):
        self.__refresh_card_list()
        valid = self.__is_valid_key()
        self.__button_apply.set_enabled(valid)
    
    def __on_attributes_changed(self):
        pass

    def __is_valid_key(self) -> bool:
        card_type = self.get_card_type()
        russian = self.get_russian()
        english = self.get_english()
        return card_type is not None and english and russian

    def __refresh_card_list(self):
        self.cards = []
        self.__layout_card_list.clear()
        card_database = self.__application.card_database
        
        card_type = self.get_card_type()
        russian = self.get_russian()
        english = self.get_english()

        for index, card in enumerate(card_database.iter_cards()):
            if self.matches(card, card_type=card_type, russian=russian, english=english):
                self.cards.append(card)
                if len(self.cards) <= 20:
                    row = self.__create_card_row(card)
                    self.__layout_card_list.add(row)

    def __create_card_row(self, card):
        row = CardRow(card)
        row.button_select.clicked.connect(
            lambda: (self.select_card(card), self.__box_russian.focus()))
        return row

    def matches(self, card, card_type, russian, english):
        russian = russian.text.lower()
        english = english.text.lower()
        if card_type is not None and card_type != card.get_word_type():
            return False
        if russian and russian not in card.get_russian().text.lower():
            return False
        if english and english not in card.get_english().text.lower():
            return False
        return card_type is not None or russian or english
