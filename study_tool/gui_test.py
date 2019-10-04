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
from study_tool.states.gui_state import GUIState


DEAD_ZONE = 0.01


class GUITesterApp(Application):

    def __init__(self):
        self.title = "GUI Test"
        Application.__init__(self, title=self.title, width=1100, height=900)
        
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.joystick_ready = False
        self.inputs = [
            Input(index=2, name="Middle", reversed=True, max=1, min=-1),
            Input(index=1, name="Left", reversed=True, max=1, min=-1),
            Input(index=3, name="Right", reversed=True, max=1, min=-1)]


        self.input.bind(pygame.K_ESCAPE, pressed=self.quit)
        self.input.key_pressed.connect(self.__on_key_pressed)
        self.input.key_released.connect(self.__on_key_released)
        self.input.mouse_pressed.connect(self.__on_mouse_pressed)
        self.input.mouse_released.connect(self.__on_mouse_released)
        self.graphics = Graphics(self.screen)

        grid_layout = widgets.GridLayout()
        grid_layout.add(widgets.Label("ID"), 0, 0)
        grid_layout.add(widgets.Label("Name"), 0, 1)
        grid_layout.add(widgets.TextEdit(), 1, 0)
        grid_layout.add(widgets.Button("Button"), 1, 1)
        grid_layout.set_column_stretch(0, 2)
        grid_layout.set_column_stretch(1, 3)

        widget = widgets.Widget()
        def callback():
            print("Pressed Ctrl+F!!!")
        widget.add_key_shortcut("Ctrl+F", callback)
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(
            widgets.Label("Combo Box:"),
            widgets.ComboBox(["Cat", "Dog", "Horse"])))
        text_edit = widgets.TextEdit()
        layout.add(text_edit)
        button = widgets.Button("Hello")
        button.clicked.connect(self.__on_button_clicked)
        layout.add(button)
        check_box = widgets.CheckBox("Check Box")
        check_box.clicked.connect(self.__on_check_box_clicked)
        layout.add(check_box)
        layout.add(grid_layout)
        layout.add(widgets.HBoxLayout(widgets.Button("Button 2!"),
                                      widgets.CheckBox("Check Box"),
                                      widgets.TextEdit()))
        layout.add(widgets.Label("This is a label"))

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

    def __on_button_clicked(self):
        print("Button clicked!")

    def __on_check_box_clicked(self):
        print("Check Box clicked!")

    def update(self, dt):
        if not self.joystick_ready:
            for axis in range(self.joystick.get_numaxes()):
                if self.joystick.get_axis(axis) != 0:
                    self.joystick_ready = True
        if self.joystick_ready:
            for index, input in enumerate(self.inputs):
                input.update(self.joystick.get_axis(input.index))
                self.state.buttons[index].update(
                    dt=dt,
                    is_down=input.amount > DEAD_ZONE,
                    is_pressed=input.amount > DEAD_ZONE and input.prev_amount <= DEAD_ZONE)

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
