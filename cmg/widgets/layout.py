import cmg
from pygame.rect import Rect
from cmg.widgets.layout_item import LayoutItem
from cmg.widgets import Widget


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

    def get_offset(self) -> cmg.Vec2:
        return cmg.Vec2(0, 0)

    def get_children(self):
        pass

    def get_visible_children(self) -> list:
        return [child for child in self.get_children() if child.is_visible()]

    def is_empty_layout(self) -> bool:
        """Returns True if this layout has no children."""
        return not self.get_visible_children()

    def is_visible(self) -> bool:
        """Returns True if this layout has children."""
        return not self.is_empty_layout()

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
        for child in self.get_visible_children():
            child.update()

    def draw(self, g):
        if not g.is_rect_in_viewport(self.get_rect()):
            return
        self.draw_children(g)

    def draw_children(self, g):
        for child in self.get_visible_children():
            child.draw(g)

    def calc_maximum_size(self) -> cmg.Vec2:
        children = self._get_layout_item_children()
        if not children:
            return cmg.Vec2(self.DEFAULT_MAX_SIZE, self.DEFAULT_MAX_SIZE)
        max_size = cmg.Vec2(0, 0)
        for child in children:
            child_max_size = child.calc_maximum_size()
            max_size.x = max(max_size.x, child_max_size.x)
            max_size.y = max(max_size.y, child_max_size.y)
        return max_size

    def calc_minimum_size(self) -> cmg.Vec2:
        children = self._get_layout_item_children()
        if not children:
            return cmg.Vec2(0, 0)
        min_size = cmg.Vec2(0, 0)
        for child in children:
            child_min_size = child.calc_minimum_size()
            min_size.x = min(min_size.x, child_min_size.x)
            min_size.y = min(min_size.y, child_min_size.y)
        return min_size

    def _get_layout_item_children(self):
        return self.get_children()

