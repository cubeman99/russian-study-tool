import pygame
import os
from cmg import widgets


class Label(widgets.Widget):
    def __init__(self,
                 text="",
                 font_family="",
                 font_size=35,
                 antialias=True,
                 text_color=(0, 0, 0)):
        super().__init__()
        height = font_size + 4
        self.set_minimum_height(height)
        self.set_maximum_height(height)

        self.antialias = antialias
        self.text_color = text_color
        self.font_size = font_size
        self.__text = text
        self.__surface = None

        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)

        # Text-surface will be created during the first update call:
        self.font_object = pygame.font.Font(None, 30)

    def get_text(self) -> str:
        return self.input_string

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        if text != self.__text:
            self.__text = text
            self.__surface = None

    def on_draw(self, g):
        if not self.__surface:
            self.__surface = self.font_object.render(
                self.__text, self.antialias, self.text_color)
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        g.draw_image(self.__surface, self.rect.left + 4, y)
