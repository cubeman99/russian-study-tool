from cmg.graphics import Graphics
from pygame.rect import Rect
from cmg import color
from cmg.widgets.layout_item import LayoutItem
from cmg.widgets import Widget
from cmg.math import Vec2
from cmg.widgets.layout import Layout


class BoxLayout(Layout):
    def __init__(self, axis=0):
        super().__init__()
        self.axis = axis
        self.children = []
        self.__stretch_factors = {}

    def remove(self, item):
        item.set_parent(None)
        self.children.remove(item)
        del self.__stretch_factors[item]

    def clear(self):
        while self.children:
            self.remove(self.children[-1])

    def add_widget(self, widget, **kwargs):
        assert isinstance(widget, Widget)
        self.add(widget, **kwargs)

    def add_layout(self, layout, **kwargs):
        assert isinstance(layout, Layout)
        self.add(layout, **kwargs)

    def add(self, item, stretch=0):
        assert item is not None
        assert stretch >= 0
        self.__stretch_factors[item] = stretch
        self.children.append(item)
        item.set_parent(self)

    def get_children(self):
        return self.children

    def on_update(self):
        if not self.children:
            return
        if self.children:
            self.__update_axis_layout(self.axis)

    def __update_axis_layout(self, axis: int):
        size = self.get_size()
        child_size = Vec2(self.get_size())
        stretch_space = size[axis]
        stretch_list = []
        stretch_factors = dict(self.__stretch_factors)

        visible_children = self.get_visible_children()

        for child in visible_children:
            stretch = stretch_factors[child]
            if stretch > 0:
                stretch_list.append(child)
            else:
                child_size[axis] = max(16, child.get_minimum_size()[axis])
                stretch_space -= child_size[axis]
                child.set_size(child_size)
        
        # If all stretch factors are 0, then make them all 1
        if not stretch_list or sum(stretch_factors.values()) == 0:
            stretch_space = size[axis]
            for child in visible_children:
                stretch_list.append(child)
                stretch_factors[child] = 1
        
        fits = False
        while not fits:
            fits = True
            stretch_sum = 0
            for child in stretch_list:
                stretch_sum += stretch_factors[child]

            if stretch_sum > 0:
                # Distribute sizes over the stretch space
                for index, child in enumerate(stretch_list):
                    stretch = stretch_factors[child]
                    if stretch != 0:
                        child_size[axis] = int(round(
                            stretch_space * (stretch / stretch_sum)))
                        child.set_size(child_size)
                        
                # Clamp sizes
                for index, child in enumerate(stretch_list):
                    child_size = child.get_size()
                    min_size = child.get_minimum_size()[axis]
                    max_size = child.get_maximum_size()[axis]
                    new_size = None
                    #if child_size[axis] < min_size:
                    #    new_size = min_size
                    if child_size[axis] > max_size:
                        new_size = max_size
                    if new_size is not None:
                        child_size[axis] = new_size
                        child.set_size(child_size)
                        del stretch_list[index]
                        stretch_space -= new_size
                        fits = False
                    else:
                        index += 1
        
        # Set final positions
        child_pos = Vec2(self.get_rect().topleft)
        for index, child in enumerate(visible_children):
            rect = child.get_rect()
            rect.topleft = child_pos.totuple()
            child_pos[axis] += child.get_size()[axis]

    def calc_maximum_size(self) -> Vec2:
        max_size = Vec2(self.DEFAULT_MAX_SIZE, self.DEFAULT_MAX_SIZE)
        max_size[self.axis] = 0
        for child in self.get_visible_children():
            child_max_size = child.calc_maximum_size()
            max_size[self.axis] += child_max_size[self.axis]
            max_size[1 - self.axis] = min(max_size[1 - self.axis],
                                            child_max_size[1 - self.axis])
        self.set_maximum_size(max_size)
        return max_size

    def calc_minimum_size(self) -> Vec2:
        if not self.children:
            return super().calc_minimum_size()
        min_size = Vec2(0, 0)
        for child in self.get_visible_children():
            child_min_size = child.calc_minimum_size()
            min_size[self.axis] += child_min_size[self.axis]
            min_size[1 - self.axis] = max(min_size[1 - self.axis],
                                            child_min_size[1 - self.axis])
        self.set_minimum_size(min_size)
        return min_size

    def __get_min(self, rect, axis):
        return rect.left if axis == 0 else rect.top

    def __get_size(self, rect, axis):
        return rect.width if axis == 0 else rect.height

    def __set_min(self, rect, axis, value):
        if axis == 0:
            rect.left = value
        else:
            rect.top = value

    def __set_size(self, rect, axis, value):
        if axis == 0:
            rect.width = value
        else:
            rect.height = value


class HBoxLayout(BoxLayout):
    def __init__(self, *items):
        super().__init__(axis=0)
        for item in items:
            self.add(item)


class VBoxLayout(BoxLayout):
    def __init__(self, *items):
        super().__init__(axis=1)
        for item in items:
            self.add(item)
