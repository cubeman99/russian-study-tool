import os
import pygame
from cmg.graphics import Graphics
from cmg import color
from cmg.color import Color
from cmg.widgets.layout_item import LayoutItem
from cmg.math import Vec2


class Font:
    def __init__(self,
                 font_size=35,
                 font_family="",
                 antialias=True,
                 text_color=(0, 0, 0)):
        self.__antialias = antialias
        self.__text_color = text_color
        self.__font_size = font_size
        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)
        self.__font = pygame.font.Font(None, self.__font_size)

    def get_pygame_font(self) -> pygame.font.Font:
        return self.__font

    def get_text_color(self) -> Color:
        return Color(self.__text_color)

    def get_size(self):
        return self.__font_size

    def set_size(self, size: int):
        if size != self.__font_size:
            self.__font_size = size
            self.__font = pygame.font.Font(None, self.__font_size)

    def measure(self, text: str) -> Vec2:
        return Vec2(self.__font.size(text))

    def render(self, text: str, color=None):
        if not color:
            color = self.__text_color
        return self.__font.render(text, self.__antialias, tuple(color))