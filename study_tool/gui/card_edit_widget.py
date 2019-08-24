from enum import IntEnum
import os
import pygame
import random
import time
from cmg import color
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool import card_attributes
from study_tool.russian.types import WordType
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.card_set import *
from study_tool.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from cmg.application import Application
from cmg.input import Keys
from cmg import widgets
from study_tool import card

class CardEditWidget(widgets.Widget):

    def __init__(self, card: Card):
        super().__init__()
        if not card:
            card = Card()
        self.__card = card

        # Create widgets
        self.__box_card_type = widgets.TextEdit()
        self.__box_english = widgets.TextEdit()
        self.__box_russian = widgets.TextEdit()
        self.__box_add_attribute = widgets.TextEdit()
        self.__button_add_attribute = widgets.Button("Add Attribute")
        self.__layout_attributes = widgets.HBoxLayout()
        self.__button_apply = widgets.Button("Apply")
        self.__button_cancel = widgets.Button("Cancel")

        self.__box_card_type.set_autocomplete_source([x.name for x in WordType])
        self.__box_add_attribute.set_autocomplete_source([x.value for x in CardAttributes])

        # Create layouts
        layout = widgets.VBoxLayout()
        layout.add_layout(widgets.HBoxLayout(widgets.Label("Type:"), self.__box_card_type))
        layout.add_layout(widgets.HBoxLayout(widgets.Label("Russian:"), self.__box_russian))
        layout.add_layout(widgets.HBoxLayout(widgets.Label("English:"), self.__box_english))
        layout.add_layout(widgets.HBoxLayout(widgets.Label("Attributes:"), self.__box_add_attribute, self.__button_add_attribute))
        layout.add_layout(widgets.HBoxLayout(self.__layout_attributes))
        layout.add_layout(widgets.HBoxLayout(self.__button_apply, self.__button_cancel))
        self.set_layout(layout)
        
        # Initialize with card data
        if self.__card.get_word_type() is not None:
            self.__box_card_type.set_text(self.__card.get_word_type().name)
        else:
            self.__box_card_type.set_text("")
        self.__box_russian.set_text(repr(self.__card.get_russian()))
        self.__box_english.set_text(repr(self.__card.get_english()))
        for attribute in self.__card.get_attributes():
            self.add_attribute(attribute)
        
        # Connect signals
        self.__box_english.text_edited.connect(self.__on_english_changed)
        self.__box_russian.text_edited.connect(self.__on_russian_changed)
        self.__box_card_type.text_edited.connect(self.__on_card_type_changed)
        self.__box_card_type.return_pressed.connect(self.__box_russian.focus)
        self.__box_russian.return_pressed.connect(self.__box_english.focus)
        self.__box_english.return_pressed.connect(self.__box_add_attribute.focus)
        self.__box_add_attribute.return_pressed.connect(self.__on_click_add_attribute)
        self.__button_add_attribute.clicked.connect(self.__on_click_add_attribute)
        self.__button_apply.clicked.connect(lambda: (self.apply, self.close))
        self.__button_cancel.clicked.connect(self.close)
        
        self.__box_card_type.focus()

    def apply(self):
        pass

    def add_attribute(self, attribute: CardAttributes):
        name = card_attributes.get_card_attribute_display_name(attribute)
        print(name)
        button = widgets.Button(name)
        button.clicked.connect(lambda: self.remove_attribute(button))
        self.__layout_attributes.add(button)

    def __on_click_add_attribute(self):
        text = self.__box_add_attribute.get_text()
        attribute = None
        try:
            attribute = CardAttributes(text)
        except:
            return
        if attribute is not None and attribute not in self.__card.get_attributes():
            self.__card.add_attribute(attribute)
            self.add_attribute(attribute)
            self.__box_add_attribute.set_text("")
            self.__box_add_attribute.focus()
            self.__box_add_attribute.set_text("")

    def remove_attribute(self, attribute_widget):
        self.__layout_attributes.remove(attribute_widget)

    def __on_english_changed(self):
        self.__on_key_changed()

    def __on_russian_changed(self):
        self.__on_key_changed()

    def __on_card_type_changed(self):
        self.__on_key_changed()

    def __on_key_changed(self):
        card_type = getattr(WordType, self.__box_card_type.get_text(), None)
        russian = self.__box_russian.get_text()
        english = self.__box_english.get_text()

        old_key = (self.__card.word_type,
                   repr(self.__card.english),
                   repr(self.__card.russian))
        new_key = (card_type, english, russian)
        valid = card_type is not None and english and russian
        if valid and new_key != old_key:
            print("Key change: {} --> {}".format(old_key, new_key))


    def get_card(self) -> Card:
        return self.__card

    def set_widget(self, card: Card):
        self.__card = card
