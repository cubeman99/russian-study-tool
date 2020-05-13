from pathlib import Path
import pygame
import queue
import time
import traceback
import cmg
from cmg.input import InputManager
from cmg.input import MouseButtons
from cmg.input import Keys
from cmg.input import KeyMods
from cmg.event import Event


class ResourceManager:

    def __init__(self):
        self.__resource_dict = {}
        self.__paths = []

    def load(self, name: str):
        return self.get(name)

    def get(self, name: str):
        if name in self.__resource_dict:
            return self.__resource_dict[name]
        res = self.load_impl(name)
        self.__resource_dict[name] = res
        return res

    def add_path(self, path: str):
        self.__paths.append(str(path))

    def resolve_path(self, path: str) -> str:
        for base in self.__paths:
            check = Path(base) / path
            if check.exists():
                return str(check)
        return str(path)

    def __getitem__(self, name: str):
        return self.get(name)


class ImageResourceManager(ResourceManager):
    def __init__(self):
        super().__init__()

    def load_impl(self, name: str):
        path = self.resolve_path(name)
        print("Loading image: " + str(path))
        return cmg.Image(path)


class Res:
    images = ImageResourceManager()
    images.add_path("data")
