import os
import pygame
from pygame import Rect
from cmg import gui
from cmg import widgets
from cmg import color
from cmg.event import Event
from cmg.input import Keys, MouseButtons

class ComboBox(widgets.Widget):
    def __init__(self, options=[], index=0):
        super().__init__()
        self.set_focusable(True)

        self.index_changed = Event()

        self.__text = ""
        self.__font = gui.Font(32)
        self.__surface = None
        self.__options = list(options)

        self.__index = 0
        if index < len(self.__options):
            self.__index = index
            self.__text = str(self.__options[index])

        size = self.__font.measure(self.__text)
        self.set_minimum_height(size.y + 4)
        self.set_maximum_height(size.y + 4)
        self.set_minimum_width(size.x + 4)
        
    def get_index(self) -> int:
        return self.__index
        
    def get_option(self):
        return self.__options[self.__index]
        
    def get_text(self) -> str:
        return self.__text

    def set_index(self, index: int):
        if index != self.__index:
            assert index >= 0
            assert index < len(self.__options)
            self.__index = index
            self.__text = str(self.__options[self.__index])
            self.__surface = None
            self.index_changed.emit()

    def set_option(self, option) -> str:
        if text in self.__options:
            self.set_index(self.__options.index(text))

    def on_key_pressed(self, key, mod, text):
        if key in [Keys.K_RIGHT, Keys.K_DOWN]:
            if self.__options:
                self.set_index((self.__index + 1) % len(self.__options))
        elif key in [Keys.K_LEFT, Keys.K_UP]:
            if self.__options:
                self.set_index((self.__index + len(self.__options) - 1)
                               % len(self.__options))
            
    def on_mouse_pressed(self, pos, button):
        pass

    def on_draw(self, g):
        if not self.__surface:
            self.__surface = self.__font.render(self.__text)
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        g.draw_image(self.__surface, self.rect.left + 4, y)