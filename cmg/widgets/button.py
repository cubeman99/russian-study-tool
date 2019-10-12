import os
import pygame
from pygame import Rect
from cmg import gui
from cmg import widgets
from cmg.color import Colors
from cmg.color import Color
from cmg.event import Event
from cmg.input import Keys
from cmg.input import MouseButtons

class Button(widgets.Widget):
    def __init__(self, text=""):
        super().__init__()
        self.set_focusable(True)

        self.clicked = Event()

        self.__text = text
        self.__font = gui.Font(32)
        self.__surface = None

        size = self.__font.measure(self.__text)
        self.set_minimum_height(size.y + 4)
        self.set_maximum_height(size.y + 4)
        self.set_minimum_width(size.x + 4)

    def get_text(self) -> str:
        return self.input_string

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        if text != self.__text:
            self.__text = text
            self.__surface = None

    def click(self):
        self.clicked.emit()

    def on_key_pressed(self, key, mod, text):
        if key in [Keys.K_RETURN, Keys.K_SPACE]:
            self.click()
            
    def on_mouse_pressed(self, pos, button):
        if button == MouseButtons.LEFT:
            self.click()

    def on_pressed(self):
        self.click()

    def on_draw(self, g):
        if not self.__surface:
            self.__surface = self.__font.render(self.__text)
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        g.fill_rect(self.get_rect(), color=Colors.YELLOW)
        r = Rect(self.get_rect())
        r.height = 4
        r.y = self.get_rect().bottom - r.height

        # Draw the box background
        c = Color(190, 205, 255)
        if self.is_focused():
            c = Color(160, 190, 255)
        g.fill_rect(self.rect, color=c)

        # Draw the text
        g.draw_image(self.__surface,
                     self.get_rect().centerx - self.__surface.get_width() / 2,
                     self.get_rect().centery - self.__surface.get_height() / 2,)

        # Draw the box border
        c = Colors.BLACK
        if self.is_focused():
            c = Colors.BLUE
        g.draw_rect(self.rect, color=c)

    def __repr__(self):
        """Returns a string representation of this object."""
        return "<{}({})>".format(self.__class__.__name__, repr(self.__text))
