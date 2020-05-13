from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from study_tool.card import *
from study_tool.card_set import *
from study_tool.entities.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.entities.study_proficiency_bar import StudyProficiencyBar


class CardListState(State):
    def __init__(self, card_set):
        super().__init__()
        self.card_set = card_set

        self.card_font = pygame.font.Font(None, 30)
        self.line_spacing = 30
        self.row_colors = [cmg.Theme.color_background,
                           cmg.Theme.color_background_light]
        self.menu = None
        self.row_unseen_color = cmg.Theme.color_background_light

    def begin(self):
        self.buttons[0] = Button("Scroll Up")
        self.buttons[1] = Button("Menu", self.pause)
        self.buttons[2] = Button("Scroll Down")

        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        viewport = pygame.Rect(0, self.margin_top, screen_width,
                               screen_height - self.margin_top - self.margin_bottom)

        self.menu = Menu(options=self.card_set.cards, viewport=viewport)
        self.menu.option_margin = 10
        self.menu.draw_menu_option_text = self.draw_menu_option_text
        self.menu.get_option_background_color = self.get_option_background_color
        self.entity_manager.add_entity(self.menu)

        g = self.app.graphics
        self.max_column_width = 0
        for card in self.card_set.cards:
            self.max_column_width = max(self.max_column_width,
                                        g.measure_text(card.get_russian(), font=self.card_font)[0])

        self.__proficiency_bar = StudyProficiencyBar(
            center_y=self.margin_top / 2,
            left=screen_center_x + 80,
            right=screen_width - 32,
            study_set=self.card_set.cards)
        self.add_entity(self.__proficiency_bar)

    def pause(self):
        self.app.push_state(SubMenuState(
            "Pause",
            [("Resume", None),
             ("Menu", self.app.pop_state),
                ("Exit", self.app.quit)]))

    def get_option_background_color(self, index, card, highlighted):
        study_data = self.app.study_database.get_card_study_data(card)
        if not study_data.is_encountered():
            row_color = self.row_unseen_color
        else:
            row_color = cmg.mathlib.lerp(Config.proficiency_level_colors[
                study_data.get_proficiency_level()], cmg.Theme.color_background, 0.7)
        if index % 2 == 1:
            row_color *= 0.94
        if highlighted:
            row_color = cmg.mathlib.lerp(row_color, cmg.Theme.color_background, 0.5)
        return row_color

    def draw_menu_option_text(self, g, option, rect, highlighted):
        card = option
        if highlighted:
            text_color = Config.option_highlighted_text_color
        else:
            text_color = Config.option_text_color

        column_1_x = rect.x + 32
        column_2_x = max(rect.x + 32 + self.max_column_width + 16,
                         rect.x + (rect.width / 2) + 32)
        center_y = rect.y + (rect.height / 2)

        g.draw_text(column_1_x, center_y,
                    text=card.get_display_text(CardSide.Russian), font=self.card_font,
                    color=text_color, align=cmg.Align.MiddleLeft)
        g.draw_text(column_2_x, center_y,
                    text=card.get_display_text(CardSide.English), font=self.card_font,
                    color=text_color, align=cmg.Align.MiddleLeft)

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2

        # Draw state
        State.draw(self, g)

        # Draw title
        g.draw_text(32, self.margin_top / 2,
                    text=self.card_set.name,
                    color=Config.title_color,
                    align=cmg.Align.MiddleLeft)
