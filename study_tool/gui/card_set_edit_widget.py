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
from study_tool.card_set import CardSet
from study_tool.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from cmg.application import Application
from cmg.input import Keys
from cmg import widgets
from study_tool import card
from study_tool.config import Config

class CardSetEditWidget(widgets.Widget):

    def __init__(self, card_set: CardSet, application):
        super().__init__()
        if not card_set:
            card_set = CardSet()
        self.__card_set = card_set
        self.__application = application

        # Create widgets
        self.__box_name = widgets.TextEdit()
        self.__button_add_card = widgets.Button("Add New Card")
        self.__button_done = widgets.Button("Done")
        self.__button_convert = widgets.Button("Assimilate to YAML")
        self.__label_card_count = widgets.Label("Cards [{}]:".format(0))
        self.__label_path = widgets.Label("")
        self.__button_convert = widgets.Button("Assimilate set to YAML")
        
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
        layout.add(self.__button_done)
        self.set_layout(layout)
        
        self.select_card_set(card_set)

        # Connect signals
        self.__button_done.clicked.connect(self.__on_click_done)
        self.__button_add_card.clicked.connect(self.__on_click_add_new_card)
        self.__button_convert.clicked.connect(self.__on_click_convert)
        
        self.__box_name.focus()

    def add_card(self, card):
        button_edit = widgets.Button("Edit")
        button_delete = widgets.Button("Remove")

        self.__layout_card_list.add(widgets.HBoxLayout(
            widgets.Label(card.get_word_type().name),
            widgets.Label(repr(card.get_russian())),
            widgets.Label(repr(card.get_english())),
            button_edit,
            button_delete
        ))

        button_edit.set_enabled(not self.__card_set.is_fixed_card_set())
        button_delete.set_enabled(not self.__card_set.is_fixed_card_set())
        
        button_edit.clicked.connect(lambda: self.__on_click_edit_card(card))
        button_delete.clicked.connect(lambda: self.__on_click_remove_card(card))

    def save(self):
        self.__application.save_card_set(self.__card_set)

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
            card_sets_in_file = self.__application.card_database.get_card_sets_from_path(old_file_path)
            if len(card_sets_in_file) > 1:
                self.__button_convert.set_text(
                    "Assimilate {} sets to YAML".format(len(card_sets_in_file)))

        self.__layout_card_list.clear()
        for card in self.__card_set.cards:
            self.add_card(card)

    def __on_click_convert(self):
        self.__application.assimilate_card_set_to_yaml(self.__card_set)
        self.select_card_set(self.__card_set)

    def __on_click_add_new_card(self):
        widget = self.__application.push_card_edit_state(Card())
        widget.updated.connect(self.__on_card_updated)

    def __on_click_edit_card(self, card: Card):
        widget = self.__application.push_card_edit_state(card)
        widget.updated.connect(self.__on_card_updated)
        
    def __on_click_remove_card(self, card: Card):
        self.__card_set.remove_card(card)
        self.save()
        self.select_card_set(self.__card_set)

    def __on_click_done(self):
        name = AccentedText(self.__box_name.get_text())
        self.__card_set.set_name(name)
        if repr(name) != repr(self.__card_set.get_name()):
            self.save()
        self.close()

    def __on_card_updated(self, card: Card):
        """Called when a card in the set is updated."""
        if self.__card_set.has_card(card):
            pass
        else:
            Config.logger.info("Added card to set: " + repr(card))
            self.__card_set.add_card(card)
            self.save()
        self.select_card_set(self.__card_set)
