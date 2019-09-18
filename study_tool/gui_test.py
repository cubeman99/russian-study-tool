import json
import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "420,80"  # Set initial window position
import pygame
import time
import shutil
import cmg
from cmg import color
import cmg.logging
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from cmg import widgets
from enum import IntEnum
from study_tool.card_set import *
from study_tool.config import Config
from study_tool.states.menu_state import MenuState
from study_tool.states.study_state import StudyState
from study_tool.states.card_list_state import CardListState
from study_tool.states.gui_state import GUIState
from study_tool.gui.card_edit_widget import CardEditWidget
from study_tool.gui.card_set_edit_widget import CardSetEditWidget
from study_tool.card_database import CardDatabase
from study_tool.scheduler import ScheduleMode
from study_tool.states.keyboard_state import KeyboardState
from study_tool.russian import conjugation
from study_tool.word_database import WordDatabase
from study_tool.example_database import ExampleDatabase
from study_tool.states.read_text_state import ReadTextState
import yaml

class GUITesterApp(Application):

    def __init__(self):
        self.title = "GUI Test"
        Application.__init__(self, title=self.title, width=1100, height=900)

        self.input.bind(pygame.K_ESCAPE, pressed=self.quit)
        self.input.key_pressed.connect(self.__on_key_pressed)
        self.input.key_released.connect(self.__on_key_released)
        self.input.mouse_pressed.connect(self.__on_mouse_pressed)
        self.input.mouse_released.connect(self.__on_mouse_released)
        self.graphics = Graphics(self.screen)

        widget = widgets.Widget()
        layout = widgets.VBoxLayout()
        text_edit = widgets.TextEdit()
        layout.add(text_edit)
        layout.add(widgets.Button("Hello"))
        layout.add(widgets.TextEdit("World"))

        scroll_area = widgets.Widget()
        scroll_layout = widgets.VBoxLayout()
        for x in range(40):
            scroll_layout.add(widgets.TextEdit("Item Number {}".format(x + 1)))
        scroll_area.set_layout(scroll_layout)
        layout.add(widgets.AbstractScrollArea(scroll_area))

        widget.set_layout(layout)
        self.state = GUIState(widget)
        self.state.init(self)
        text_edit.focus()

    def update(self, dt):
        self.state.process_input()
        self.state.update(dt)

    def draw(self):
        self.graphics.clear(color.WHITE)
        self.state.draw(self.graphics)

    def __on_key_pressed(self, key, mod, text):
        self.state.on_key_pressed(key, mod, text)

    def __on_key_released(self, key, mod):
        self.state.on_key_released(key, mod)

    def __on_mouse_pressed(self, pos, button):
        self.state.on_mouse_pressed(pos, button)

    def __on_mouse_released(self, pos, button):
        self.state.on_mouse_released(pos, button)


if __name__ == "__main__":
    app = StudyCardsApp()
    app.run()
