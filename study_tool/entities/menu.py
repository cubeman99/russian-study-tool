from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg import math
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.config import Config
from study_tool.entities.entity import Entity


class Menu(Entity):
    def __init__(self, options, viewport):
        super().__init__()
        self.cursor = 0.0
        self.options = list(options)
        self.viewport = viewport
        self.option_font = pygame.font.Font(None, 42)
        self.option_spacing = 40
        self.option_margin = 48
        self.scroll_position = 0.0
        self.option_border_thickness = 4

    def selected_option(self):
        option_index = int(round(self.cursor))
        return self.options[option_index]

    def get_option_background_color(self, index, option, highlighted=False):
        if highlighted:
            return Config.option_highlighted_background_color
        else:
            return Config.option_background_colors[index % 2]

    def get_option_border_color(self, index, option, highlighted=False):
        if highlighted:
            return Config.option_highlighted_border_color
        else:
            return Config.option_border_colors[index % 2]

    def draw_menu_option_text(self, g, option, rect, highlighted=False):
        if highlighted:
            text_color = Config.option_highlighted_text_color
        else:
            text_color = Config.option_text_color
        if isinstance(option, tuple):
            option = option[0]
        g.draw_text(rect.x + 16, rect.y + (rect.height / 2),
                    text=str(option), font=self.option_font,
                    color=text_color, align=Align.MiddleLeft)

    def update(self, dt):
        app = self.context
        move = app.inputs[2].get_amount() - app.inputs[0].get_amount()
        speed = 10.0
        self.cursor += move * dt * speed
        if self.cursor < 0.5:
            self.cursor += len(self.options)
        if self.cursor > len(self.options) - 0.5:
            self.cursor -= len(self.options)

        option_list_height = len(self.options) * self.option_spacing
        option_area_height = self.viewport.height
        if option_list_height > option_area_height:
            desired_scroll_position = (((self.cursor + 0.5) * self.option_spacing) -
                                       option_area_height / 2)
            desired_scroll_position = max(0, desired_scroll_position)
            desired_scroll_position = min(desired_scroll_position,
                                          option_list_height - option_area_height)
            self.scroll_position = cmg.math.lerp(
                self.scroll_position,
                desired_scroll_position,
                0.2)
            if abs(self.scroll_position - desired_scroll_position) < 2:
                self.scroll_position = desired_scroll_position
        else:
            self.scroll_position = 0

    def draw(self, g):
        top = -self.scroll_position
        option_index = int(round(self.cursor))
        option_top = self.viewport.y + top
        row_width = self.viewport.width - (self.option_margin * 2)
        border_row_width = row_width + (self.option_border_thickness * 2)

        # Draw the cursor
        cursor_y = option_top + ((self.cursor + 0.5) * self.option_spacing)
        g.fill_rect(self.viewport.x + self.option_margin -
                    self.option_border_thickness - Config.option_cursor_width,
                    cursor_y - (Config.option_cursor_height / 2),
                    border_row_width + (Config.option_cursor_width * 2),
                    Config.option_cursor_height,
                    color=Config.option_cursor_color)

        # Draw menu options
        for index, option in enumerate(self.options):
            y = option_top + (index * self.option_spacing)
            center_y = y + (self.option_spacing / 2)
            highlighted = index == option_index
            row_color = self.get_option_background_color(
                index, option, highlighted)
            border_color = self.get_option_border_color(
                index, option, highlighted)
            row_rect = pygame.Rect(self.viewport.x + self.option_margin, y,
                                   row_width, self.option_spacing)

            # Draw the option border
            border_rect = pygame.Rect(row_rect)
            border_rect.inflate_ip(self.option_border_thickness * 2, 0)
            if index == 0:
                border_rect.y -= self.option_border_thickness
                border_rect.height += self.option_border_thickness
            if index == len(self.options) - 1:
                border_rect.height += self.option_border_thickness
            g.fill_rect(border_rect, color=border_color)

            # Draw the row background
            g.fill_rect(row_rect, color=row_color)

            # Draw the option name
            self.draw_menu_option_text(g, option, row_rect,
                                       highlighted=highlighted)
