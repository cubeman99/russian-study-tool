import pygame
import os
from cmg import widgets
from cmg import gui

class Label(widgets.Widget):
    def __init__(self, text=""):
        super().__init__()
        self.__text = text
        self.__font = gui.Font(32)
        self.__surface = None
        self.__update_size()

    def get_text(self) -> str:
        return self.__text

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        if text != self.__text:
            self.__text = text
            self.__surface = None
            self.__update_size()

    def __update_size(self):
        size = self.__font.measure(self.__text)
        self.set_minimum_height(size.y + 4)
        self.set_maximum_height(size.y + 4)
        self.set_minimum_width(size.x + 4)

    def on_draw(self, g):
        if not self.__surface:
            self.__surface = self.__font.render(self.__text)
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        g.draw_image(self.__surface, self.rect.left + 4, y)
