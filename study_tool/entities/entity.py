from cmg.math import Vec2
from cmg.math import Rect

class Entity:
    """
    A single entity.
    """

    def __init__(self):
        super().__init__()
        self.__visible = True
        self.__destroyed = False
        self.__position = Vec2(0, 0)
        self.__size = Vec2(0, 0)
        self.__manager = None
        self.__context = None
        self.__parent = None
        self.__children = []

    @property
    def context(self):
        return self.__context

    def get_x(self):
        return self.__position.x

    def get_y(self):
        return self.__position.y

    def get_width(self):
        return self.__size.x

    def get_height(self):
        return self.__size.y

    def get_position(self) -> Vec2:
        return self.__position

    def get_center(self) -> Vec2:
        return self.__position + (self.__size * 0.5)

    def get_size(self) -> Vec2:
        return self.__size

    def get_rect(self) -> Rect:
        return Rect(self.__position.x, self.__position.y,
                    self.__size.x, self.__size.y)

    def is_destroyed(self) -> bool:
        return self.__destroyed

    def is_visible(self) -> bool:
        return self.__visible

    def get_parent(self):
        return self.__parent

    def get_children(self) -> list:
        return self.__children

    def add_child(self, entity, **kwargs):
        assert entity not in self.__children
        self.__children.append(entity)
        entity.__parent = self
        entity.init(manager=self.__manager, context=self.__context, **kwargs)
        return entity

    def remove_child(self, entity):
        assert entity in self.__children
        self.__children.remove(entity)
        entity.__parent = None
        entity.__context = None
        entity.__manager = None
        return entity

    def destroy_children(self):
        for child in self.__children:
            child.destroy()

    def set_x(self, x):
        self.__position.x = x

    def set_y(self, y):
        self.__position.y = y

    def set_position(self, position: Vec2, y=None):
        if y is None:
            self.__position = Vec2(position)
        else:
            self.__position = Vec2(position, y)

    def set_size(self, size: Vec2, height=None):
        if height is None:
            self.__size = Vec2(size)
        else:
            self.__size = Vec2(size, height)

    def set_rect(self, x, y=None, width=None, height=None):
        if y is None:
            self.__position = Vec2(x.left, x.top)
            self.__size = Vec2(x.width, x.height)
        elif width is None:
            self.__position = Vec2(x)
            self.__size = Vec2(y)
        else:
            self.__position = Vec2(x, y)
            self.__size = Vec2(width, height)

    def set_visible(self, visible: bool):
        self.__visible = visible

    def destroy(self):
        self.__destroyed = True
        self.on_destroy()

    def on_create(self):
        pass

    def on_destroy(self):
        pass

    def update(self, dt: float):
        pass

    def draw(self, g):
        pass

    def init(self, manager, context, pos=None):
        self.__manager = manager
        self.__context = context
        self.__destroyed = False
        if pos is not None:
            self.__position = Vec2(pos)
        self.on_create()
