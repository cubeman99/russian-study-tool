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
from cmg.math import Vec2
from study_tool.card import *
from study_tool.card_set import *
from study_tool.entities.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState


class KeyboardState(State):
    def __init__(self):
        super().__init__()

    def begin(self):
        self.buttons[0] = Button("Scroll Up")
        self.buttons[1] = Button("Menu", self.click)
        self.buttons[2] = Button("Scroll Down")
        self.button_width = 64
        self.button_height = 64
        self.cursor_position = Vec2(0, 0)
        self.text = ""
        self.grid = [" йцукенгшщзх",
                     " фывапролджэ",
                     " ячсмитьбюёъ"]
        self.grid = [" qwertyuiop",
                     " asdfghjkl;",
                     " zxcvbnm,./"]
        self.grid = [" f",
                     "xe",
                     "sd",
                     "mc",
                     "gb",
                     "aa"]
        self.grid_width = len(self.grid[0])
        self.grid_height = len(self.grid)
        self.grid_size = [self.grid_width, self.grid_height]
        self.click_timer = 0
        for r in range(0, len(self.grid)):
            self.grid[r] = [c for c in self.grid[r]]
        #self.grid[1][0] = ("<", self.backspace)
        #self.grid[2][0] = (" ", lambda: None)

    def backspace(self):
        if len(self.text) > 0:
            self.text = self.text[:-1]

    def click(self):
        cursor_grid_x = int(self.cursor_position[0])
        cursor_grid_y = int(self.cursor_position[1])
        #c = self.grid[cursor_grid_y][cursor_grid_x]
        # if isinstance(c, tuple):
        #  c[1]()
        # else:
        #  self.text += c

    def update(self, dt):
        move = (self.app.inputs[0].get_amount(),
                self.app.inputs[2].get_amount())
        speed = 20.0
        prev_cursor_position = Vec2(self.cursor_position)
        self.click_timer += dt

        for i in range(2):
            self.cursor_position[i] -= move[i] * dt * speed
            if self.cursor_position[i] < 0:
                self.cursor_position[i] += self.grid_size[1]
        #self.cursor_position.x = (1 - self.app.inputs[0].get_amount()) * self.grid_height * 0.999
        #self.cursor_position.y = (1 - self.app.inputs[2].get_amount()) * self.grid_height * 0.999
        distance = (self.cursor_position - prev_cursor_position).length()
        if distance > 0.1:
            self.click_timer = 0
        else:
            self.click_timer += dt
            if self.click_timer > 1.0:
                self.click()
                self.click_timer = 0.0

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2

        # Draw the keyboard
        gx = screen_center_x - (self.grid_width * self.button_width) / 2
        gy = screen_center_y - (self.grid_height * self.button_height) / 2
        cursor_grid_x = int(self.cursor_position[0])
        cursor_grid_y = int(self.cursor_position[1])
        for grid_y in range(0, self.grid_height):
            for grid_x in range(0, self.grid_width):
                x = gx + grid_x * self.button_width
                y = gy + grid_y * self.button_height
                cx = x + (self.button_width / 2)
                cy = y + (self.button_height / 2)
                back_color = color.WHITE
                border_color = color.BLACK
                selected = False
                if grid_x == 0:
                    selected = grid_y == cursor_grid_x
                else:
                    selected = grid_y == cursor_grid_y
                if selected:
                    back_color = color.YELLOW
                    border_color = color.BLUE
                g.fill_rect(x, y, self.button_width,
                            self.button_height, color=back_color)
                if selected:
                    t = self.click_timer / 1.0
                    g.fill_rect(x, y, int(self.button_width * t),
                                self.button_height, color=color.WHITE)
                g.draw_rect(x, y, self.button_width,
                            self.button_height, color=border_color)
                c = self.grid[grid_y][grid_x]
                if isinstance(c, tuple):
                    c = c[0]
                g.draw_text(cx, cy, text=c, color=color.BLACK,
                            align=Align.Centered)

        x = gx + 0.5 * self.button_width
        y = gy + self.cursor_position[0] * self.button_height
        g.fill_rect(x, y, 4, 4, color=color.BLUE)
        x = gx + 1.5 * self.button_width
        y = gy + self.cursor_position[1] * self.button_height
        g.fill_rect(x, y, 4, 4, color=color.BLUE)

        # Draw state
        State.draw(self, g)

        g.draw_text(screen_center_x, self.margin_top / 2,
                    text=self.text + "_", color=color.BLACK,
                    align=Align.Centered)
