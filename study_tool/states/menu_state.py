from enum import IntEnum
import os
import pygame
import random
import time
import threading
import cmg
from cmg import math
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.config import Config
from study_tool.card import Card
from study_tool.card_set import CardSide
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetPackage
from study_tool.entities.menu import Menu
from study_tool.states.read_text_state import ReadTextState
from study_tool.states.state import *
from study_tool.states.study_state import StudyParams
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.scheduler import SchedulerParams
from study_tool.entities.study_proficiency_bar import StudyProficiencyBar
from study_tool.gui.query_widget import QueryWidget
from study_tool.gui.create_card_set_widget import CreateCardSetWidget
from study_tool.query import CardQuery


class MenuState(State):
    """
    Menu state for browsing card sets and packages.
    """
    def __init__(self, package: CardSetPackage):
        super().__init__()
        self.package = package

        self.buttons[0] = Button("Up")
        self.buttons[1] = Button("Select", self.__select)
        self.buttons[2] = Button("Down")

        self.title = None
        self.top_level = package.parent == None
        self.title_font = pygame.font.Font(None, 50)
        self.option_font = pygame.font.Font(None, 42)
        self.option_spacing = 40
        self.option_margin = 48
        self.option_border_thickness = 4
        self.menu = None

        self.__metrics = None
        self.__bars = []
        self.__dirty_metrics_set = set()
        self.__lock_dirty = threading.Lock()

    def begin(self):
        self.__bars = []
        self.title = (self.app.title if self.package.parent is None
                      else self.package.name)

        screen_width, screen_height = self.app.screen.get_size()
        viewport = pygame.Rect(0, self.margin_top, screen_width,
                               screen_height - self.margin_top - self.margin_bottom)
        
        self.__metrics = self.app.study_database.get_group_study_metrics(self.package)
        self.__dirty_metrics_set = set()

        # Create menu options
        self.menu = Menu(options=[], viewport=viewport)
        self.entity_manager.add_entity(self.menu)
        self.menu.draw_menu_option_text = self.draw_menu_option_text
        self.menu.options = []
        if self.top_level:
            self.menu.options.append(("Quit", self.app.pop_state))
            self.menu.options.append(("Card Editor", self.__open_card_editor))
            self.menu.options.append(("Story Mode", self.__open_study_mode))
        else:
            self.menu.options.append(("Back", self.app.pop_state))
        for package in self.package.packages:
            bar = StudyProficiencyBar(package)
            bar.init(None, self.app)
            self.__bars.append(bar)
            self.menu.options.append(
                ("[...] {}".format(package.name), package, bar))
        for card_set in self.package.card_sets:
            name = card_set.name
            if card_set.is_fixed_card_set():
                name += " [txt]"
            bar = StudyProficiencyBar(card_set)
            bar.init(None, self.app)
            self.__bars.append(bar)
            self.menu.options.append((name, card_set, bar))
        self.menu.options.append(
            ("Study all " + self.package.name, self.package))
        
        # Create proficiency bar
        title_left = self.option_margin
        title_right = title_left + Graphics(None).measure_text(
            text=self.title, font=self.title_font)[0]
        bar = StudyProficiencyBar(
            center_y=self.margin_top / 2,
            left=max(screen_width * 0.6, title_right + 32),
            right=screen_width - 32,
            study_set=self.package)
        self.__bars.append(bar)
        self.entity_manager.add_entity(bar)

        # Connect signals
        self.app.study_database.card_study_data_changed.connect(
            self.__on_card_study_data_changed)
        self.app.card_database.card_added_to_set.connect(
            self.__on_card_added_or_removed_to_set)
        self.app.card_database.card_removed_from_set.connect(
            self.__on_card_added_or_removed_to_set)
        self.app.card_database.card_set_created.connect(
            self.__on_card_set_created)

    def update(self, dt):
        State.update(self, dt)

        # Recalculate metrics
        with self.__lock_dirty:
            for bar in self.__dirty_metrics_set:
                bar.recalculate()
                if bar.study_set == self.package:
                    self.__metrics = self.app.study_database.get_group_study_metrics(self.package)
            self.__dirty_metrics_set.clear()
            
    def draw_menu_option_text(self, g, option, rect, highlighted):
        name = option[0]
        value = option[1]
        bar = None
        if len(option) > 2:
            bar = option[2]
        if highlighted:
            text_color = Config.option_highlighted_text_color
        else:
            text_color = Config.option_text_color

        # Draw the option name
        center_y = rect.y + (rect.height / 2)
        g.draw_text(rect.x + 16,
                    center_y,
                    text=name,
                    font=self.option_font,
                    color=text_color,
                    align=Align.MiddleLeft)

        # Draw the completion bar
        if bar:
            bar.center_y = center_y
            bar.left = int(rect.x + (rect.width * 0.6))
            bar.right = rect.x + rect.width - 16
            bar.draw(g)

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2

        # Draw the state
        State.draw(self, g)

        # Draw title
        title_left = self.option_margin
        title_right = title_left + g.measure_text(text=self.title,
                                                  font=self.title_font)[0]
        g.draw_text(title_left, self.margin_top / 2,
                    text=self.title,
                    font=self.title_font,
                    color=Config.title_color,
                    align=Align.MiddleLeft)

        g.draw_text(screen_center_x, self.margin_top / 2,
                    text="{:.0f} / {:.0f}".format(self.__metrics.get_proficiency_count(),
                                                  self.__metrics.history_score),
                    font=self.title_font,
                    color=Config.title_color,
                    align=Align.Centered)

    def __open_study_mode(self):
        self.app.push_state(ReadTextState())

    def __open_set(self, card_set):
        options = [
            ("Quiz Random Sides",
             lambda: self.app.push_study_state(
                 card_set=card_set,
                 study_params=StudyParams(random_side=True))),
            ("Quiz Random Forms",
                lambda: self.app.push_study_state(
                    card_set=card_set,
                    study_params=StudyParams(random_side=True,
                                             random_form=True))),
            ("Quiz English",
                lambda: self.app.push_study_state(
                    card_set=card_set,
                    study_params=StudyParams(shown_side=CardSide.English))),
            ("Quiz Russian",
                lambda: self.app.push_study_state(
                    card_set=card_set,
                    study_params=StudyParams(shown_side=CardSide.Russian))),
            ("Quiz New Cards",
                lambda: self.app.push_study_state(
                    card_set=card_set,
                    card_query=CardQuery(max_proficiency=0),
                    study_params=StudyParams(random_side=True),
                    scheduler_params=SchedulerParams(max_repetitions=1))),
            ("Quiz Problem Cards",
                lambda: self.app.push_study_state(
                    card_set=card_set,
                    card_query=CardQuery(max_score=0.9),
                    study_params=StudyParams(random_side=True))),
            ("Query",
                lambda: self.app.push_gui_state(QueryWidget(self.app, card_set))),
            ("List", lambda: self.app.push_card_list_state(card_set)),
            ("Edit", lambda: self.app.push_card_set_edit_state(card_set))]
        if card_set is self.package:
            options.append(("Create New Set", lambda: self.app.push_gui_state(
                CreateCardSetWidget(self.package))))
        if isinstance(card_set, CardSet) and card_set.is_fixed_card_set():
            old_file_path = card_set.get_file_path()
            card_sets_in_file = self.app.card_database.get_card_sets_from_path(old_file_path)
            if len(card_sets_in_file) > 1:
                text = "Assimilate {} sets to YAML".format(len(card_sets_in_file))
            else:
                text = "Assimilate to YAML"
            options.append((text, lambda: self.app.assimilate_card_set_to_yaml(card_set)))

        options += [("Cancel", None)]
        self.app.push_state(SubMenuState(card_set.name, options))

    def __select(self):
        values = self.menu.selected_option()
        option = values[0]
        action = values[1]
        if isinstance(action, CardSetPackage):
            if action == self.package:
                self.__open_set(action)
            else:
                self.app.push_state(MenuState(action))
        elif isinstance(action, CardSet):
            self.__open_set(action)
        else:
            action()

    def __open_card_editor(self):
        self.app.push_card_edit_state(
            Card(),
            close_on_apply=False,
            allow_card_change=True)

    def __on_card_study_data_changed(self, card: Card, card_study_data):
        """Called when a card's study data changes."""
        for bar in self.__bars:
            if bar.study_set.has_card(card):
                with self.__lock_dirty:
                    self.__dirty_metrics_set.add(bar)

    def __on_card_added_or_removed_to_set(self, card: Card, card_set: CardSet):
        """Called when a card is added to a card set."""
        for bar in self.__bars:
            if bar.study_set == card_set:
                with self.__lock_dirty:
                    self.__dirty_metrics_set.add(bar)

    def __on_card_set_created(self, card_set: CardSet):
        """Called when a card set is created."""

                    