from pygame.rect import Rect
import abc
import cmg


class LayoutItem:
    DEFAULT_MAX_SIZE = 16777215

    def __init__(self):
        super().__init__()
        self.parent = None
        self.rect = Rect(80, 200, 200, 60)
        self.__maximum_size = cmg.Vec2(
            self.DEFAULT_MAX_SIZE, self.DEFAULT_MAX_SIZE)
        self.__minimum_size = cmg.Vec2(10, 10)

    @abc.abstractclassmethod
    def _get_layout_item_children(self):
        return []

    @abc.abstractclassmethod
    def calc_maximum_size(self) -> cmg.Vec2:
        pass

    @abc.abstractclassmethod
    def calc_minimum_size(self) -> cmg.Vec2:
        pass

    @abc.abstractclassmethod
    def is_visible(self) -> bool:
        """Returns True if this item is visible."""
        return self.__visible

    def get_maximum_size(self) -> cmg.Vec2:
        return self.__maximum_size

    def get_maximum_width(self) -> int:
        return self.__maximum_size.x

    def get_maximum_height(self) -> int:
        return self.__maximum_size.y

    def get_minimum_size(self) -> cmg.Vec2:
        return self.__minimum_size

    def get_minimum_width(self) -> int:
        return self.__minimum_size.x

    def get_minimum_height(self) -> int:
        return self.__minimum_size.y

    def get_rect(self) -> Rect:
        return self.rect

    def get_width(self) -> int:
        return self.rect.width

    def get_height(self) -> int:
        return self.rect.height

    def get_size(self) -> cmg.Vec2:
        return cmg.Vec2(self.rect.size)

    def get_root_parent(self):
        if self.parent:
            return self.parent.get_root_parent()
        return self

    def iter_widgets(self):
        raise NotImplementedError()

    def set_rect(self, rect: Rect):
        self.rect = Rect(rect)

    def set_size(self, size):
        self.rect.size = cmg.Vec2(size).totuple()

    def set_maximum_size(self, size):
        self.__maximum_size = cmg.Vec2(size)

    def set_maximum_width(self, width):
        self.__maximum_size.x = width

    def set_maximum_height(self, height):
        self.__maximum_size.y = height

    def set_minimum_size(self, size):
        self.__minimum_size = cmg.Vec2(size)

    def set_minimum_width(self, width):
        self.__minimum_size.x = width

    def set_minimum_height(self, height):
        self.__minimum_size.y = height

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        if parent != self.parent:
            self.parent = parent
