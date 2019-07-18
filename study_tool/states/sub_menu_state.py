from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg.application import *
from cmg.graphics import *
from cmg.input import *
from study_tool.config import Config
from study_tool.menu import Menu
from study_tool.states.state import *


class SubMenuState(State):
    def __init__(self, title, options=()):
        super().__init__()
        self.draw_state_below = True
        self.title = title
        self.options = list(options)
        self.width = None
        self.height = None
        self.title_font = pygame.font.Font(None, 50)
        self.option_font = pygame.font.Font(None, 42)
        self.background_color = Config.background_color
        self.border_color = Config.window_border_color
        self.title_color = Config.title_color
        self.menu = None
        self.window_margin_top = 100
        self.window_margin_sides = 24

    def begin(self):
        self.buttons[0] = Button("Up")
        self.buttons[1] = Button("Select", self.select)
        self.buttons[2] = Button("Down")

        self.menu = Menu(options=self.options, viewport=None)
        self.menu.option_margin = 8
        if self.height is None:
            self.height = ((len(self.options) * self.menu.option_spacing) +
                           self.window_margin_top + self.window_margin_sides)
        if self.width is None:
            self.width = 400
            self.width = max(self.width,
                             self.app.graphics.measure_text(self.title, font=self.title_font)[0] +
                             (self.window_margin_sides * 2))

        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        window_rect = pygame.Rect(
            screen_center_x - (self.width / 2),
            screen_center_y - (self.height / 2),
            self.width, self.height)
        self.menu.viewport = pygame.Rect(
            window_rect.x + self.window_margin_sides,
            window_rect.y + self.window_margin_top,
            window_rect.width - (self.window_margin_sides * 2),
            window_rect.height - self.window_margin_top - self.window_margin_sides)

    def select(self):
        option, action = self.menu.selected_option()
        self.app.pop_state()
        if action is not None:
            action()

    def update(self, dt):
        self.menu.update_menu(app=self.app, dt=dt)

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        window_rect = pygame.Rect(
            screen_center_x - (self.width / 2),
            screen_center_y - (self.height / 2),
            self.width, self.height)

        # Draw the window box
        g.fill_rect(window_rect, color=self.background_color)
        g.draw_rect(window_rect, color=self.border_color,
                    thickness=Config.window_border_thickness)

        # Draw the title
        g.draw_text(x=window_rect.x + (window_rect.width / 2),
                    y=window_rect.y + (self.window_margin_top / 2),
                    text=self.title,
                    font=self.title_font,
                    color=self.title_color,
                    align=Align.Centered)

        # Draw the list of menu options
        self.menu.draw_menu(g)
