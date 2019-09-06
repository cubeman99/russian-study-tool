from cmg.math import Vec2

class Entity:
    """
    A single entity.
    """

    def __init__(self):
        super().__init__()
        self.__visible = True
        self.__destroyed = False
        self.__position = Vec2(0, 0)
        self.__manager = None
        self.__context = None

    @property
    def context(self):
        return self.__context

    def get_position(self) -> Vec2:
        return self.__position

    def is_destroyed(self) -> bool:
        return self.__destroyed

    def is_visible(self) -> bool:
        return self.__visible

    def set_position(self, position: Vec2):
        self.__position = position

    def set_visible(self, visible: bool):
        self.__visible = visible

    def destroy(self):
        self.__destroyed = True

    def update(self, dt: float):
        pass

    def draw(self, g):
        pass

    def init(self, manager, context, pos: Vec2):
        self.__manager = manager
        self.__context = context
        self.__destroyed = False
        if pos is not None:
            self.__position = Vec2(pos)
