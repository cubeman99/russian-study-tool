from enum import IntEnum
import os
import pygame
from pygame import Rect
import cmg
from cmg import gui
from cmg import widgets
from cmg.event import Event
from cmg.input import Keys, MouseButtons


class ComboBox(widgets.Widget):
    def __init__(self, options=[], index=0):
        super().__init__()
        self.set_focusable(True)

        self.index_changed = Event()

        self.__image = cmg.Res.images[cmg.Theme.image_scrollbar_arrow_down]
        self.__text = ""
        self.__font = cmg.Font(32)
        self.__surface = None
        self.__options = []
        for option in options:
            self.__options.append(option)

        self.__index = 0
        if index < len(self.__options):
            self.__index = index
            self.__text = self.__get_option_text(self.__options[index])

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
            self.__text = self.__get_option_text(self.__options[self.__index])
            self.__surface = None
            self.index_changed.emit()

    def set_option(self, option) -> str:
        if option in self.__options:
            self.set_index(self.__options.index(option))

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

    def on_pressed(self):
        self.set_index((self.__index + 1) % len(self.__options))

    def on_draw(self, g):
        # Render the text
        if not self.__surface:
            self.__surface = self.__font.render(
                self.__text, color=cmg.Theme.color_text)
            
        # Draw the box background
        g.fill_rect(self.rect, color=cmg.Theme.color_combo_box_background)

        # Draw the text
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        g.draw_image(self.__surface, self.rect.left + 4, y)
        
        # Draw the box border
        c = cmg.Theme.color_outline
        if self.is_focused():
            c = cmg.Theme.color_outline_focused
        g.draw_rect(self.rect, color=c)
        
        # Draw the arrow image
        if self.__image:
            image_rect = Rect(self.get_rect())
            image_rect.width = image_rect.height
            image_rect.left = self.get_rect().right - image_rect.width
            g.draw_image(self.__image, image_rect)

    def __get_option_text(self, option) -> str:
        if isinstance(option, IntEnum):
            return option.name
        return str(option)
