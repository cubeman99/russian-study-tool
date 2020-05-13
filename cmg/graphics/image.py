import pygame
from pygame import Rect
from enum import IntFlag
import cmg
from cmg.color import Colors

class Image:

    def __init__(self, path: str):
        self.__surface = pygame.image.load(str(path))

    def get_size(self) -> tuple:
        return (self.width, self.height)

    @property
    def width(self) -> int:
        return self.__surface.width

    @property
    def height(self) -> int:
        return self.__surface.height

    def get_surface(self) -> pygame.Surface:
        return self.__surface
