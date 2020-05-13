import os
import pygame
from pygame import Rect
from cmg import gui
from cmg import widgets
from cmg.event import Event
from cmg.input import Keys
from cmg.input import MouseButtons

class ImageView(widgets.Widget):
    def __init__(self, image=None):
        super().__init__()
        self.__image = image
        w = 32
        h = 32
        self.set_minimum_width(w)
        self.set_minimum_height(h)
        self.set_maximum_width(w)
        self.set_maximum_height(h)

    def on_draw(self, g):
        if not self.__image:
            return
        rect = self.get_rect()
        w, h = self.__image.get_size()
        image = pygame.transform.scale(self.__image, (rect.width, rect.height))
        g.draw_image(image, (rect.x, rect.y))
