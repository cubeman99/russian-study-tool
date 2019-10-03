from cmg.graphics import Graphics
from pygame.rect import Rect
from cmg import color
from cmg.widgets.layout_item import LayoutItem
from cmg.widgets import Widget
from cmg.math import Vec2


class Layout(LayoutItem):
    def __init__(self):
        super().__init__()
        self.rect = Rect(4, 5, 5, 5)

    def iter_widgets(self):
        for child in self.get_children():
            if isinstance(child, Widget):
                yield child
            for widget in child.iter_widgets():
                yield widget

    def get_offset(self) -> Vec2:
        return Vec2(0, 0)

    def get_children(self):
        pass

    def iter_child_widgets(self):
        for child in self.get_children():
            for widget in child.iter_child_widgets():
                yield widget

    def on_update(self):
        pass

    def update(self):
        self.on_update()
        self.update_children()

    def update_children(self):
        for child in self.get_children():
            child.update()

    def draw(self, g):
        if not g.is_rect_in_viewport(self.get_rect()):
            return
        self.draw_children(g)

    def draw_children(self, g):
        for child in self.get_children():
            child.draw(g)

    def calc_maximum_size(self) -> Vec2:
        max_size = Vec2(0, 0)
        for child in self._get_layout_item_children():
            child_max_size = child.calc_maximum_size()
            max_size.x = max(max_size.x, child_max_size.x)
            max_size.y = max(max_size.y, child_max_size.y)
        return max_size

    def calc_minimum_size(self) -> Vec2:
        min_size = Vec2(0, 0)
        for child in self._get_layout_item_children():
            child_min_size = child.calc_minimum_size()
            min_size.x = min(min_size.x, child_min_size.x)
            min_size.y = min(min_size.y, child_min_size.y)
        return min_size

    def _get_layout_item_children(self):
        return self.get_children()


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

    def add(self, item, stretch=1):
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
        self.update_axis_layout(self.axis)

    def update_axis_layout(self, axis: int):
        size = self.get_size()
        child_size = Vec2(self.get_size())
        stretch_space = size[axis]
        stretch_list = []

        stretch_factor_total = sum(self.__stretch_factors.values())

        for index, child in enumerate(self.children):
            stretch = self.__stretch_factors[child]
            if stretch == 0:
                child_size[axis] = max(16, child.get_minimum_size()[axis])
                stretch_space -= child_size[axis]
                child.set_size(child_size)
            else:
                stretch_list.append(child)
        
        fits = False
        while not fits:
            fits = True
            stretch_sum = 0
            for child in stretch_list:
                stretch_sum += self.__stretch_factors[child]

            if stretch_sum > 0:
                # Distribute sizes over the stretch space
                for index, child in enumerate(stretch_list):
                    stretch = self.__stretch_factors[child]
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
        for index, child in enumerate(self.children):
            rect = child.get_rect()
            rect.topleft = child_pos.totuple()
            child_pos[axis] += child.get_size()[axis]

        return

        child_pos = Vec2(self.get_rect().topleft)
        for index, child in enumerate(self.children):
            rect = child.get_rect()
            rect.topleft = child_pos.totuple()
            child_pos[axis] += child.get_size()[axis]


        fits = False
        while not fits:
            fits = True
            remain_space = stretch_space
            for index, child in enumerate(stretch_list):
                remain_count = sum(self.__stretch_factors[x]
                                   for x in stretch_list[index:])
                #remain_count = len(stretch_list) - index
                child_size[axis] = int(round(remain_space / remain_count))
                child.set_size(child_size)
                remain_space -= child_size[axis]

            index = 0
            while index < len(stretch_list):
                child = stretch_list[index]
                new_size = None
                min_size = child.get_minimum_size()[axis]
                max_size = child.get_maximum_size()[axis]
                if child.get_size()[axis] < min_size:
                    new_size = min_size
                if child.get_size()[axis] > max_size:
                    new_size = max_size
                if new_size is not None:
                    child_size[axis] = new_size
                    child.set_size(child_size)
                    del stretch_list[index]
                    stretch_space -= new_size
                    fits = False
                else:
                    index += 1

        child_pos = Vec2(self.get_rect().topleft)
        for index, child in enumerate(self.children):
            rect = child.get_rect()
            rect.topleft = child_pos.totuple()
            child_pos[axis] += child.get_size()[axis]

    def calc_maximum_size(self) -> Vec2:
        max_size = Vec2(self.DEFAULT_MAX_SIZE, self.DEFAULT_MAX_SIZE)
        for child in self.children:
            child_max_size = child.calc_maximum_size()
            max_size[self.axis] += child_max_size[self.axis]
            max_size[1 - self.axis] = min(max_size[1 - self.axis],
                                          child_max_size[1 - self.axis])
        self.set_maximum_size(max_size)
        return max_size

    def calc_minimum_size(self) -> Vec2:
        min_size = Vec2(0, 0)
        for child in self.children:
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
