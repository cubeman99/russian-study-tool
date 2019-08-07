from cmg.graphics import Graphics
from pygame.rect import Rect
from cmg import color
from cmg.widgets.layout_item import LayoutItem
from cmg.math import Vec2


class Widget(LayoutItem):
    def __init__(self):
        super().__init__()
        self.layout = None
        self.rect = Rect(80, 200, 200, 60)
        self.focused_widget = None
        self.focused = False
        self.focusable = False

    def get_layout(self):
        return self.layout

    def get_focusable(self) -> bool:
        return self.focusable

    def set_focusable(self, focusable: bool):
        self.focusable = focusable

    def change_focus(self, widget):
        if self.focused_widget:
            self.focused_widget.focused = False
            self.focused_widget.on_lose_focus()
        self.focused_widget = widget
        if self.focused_widget:
            self.focused_widget.focused = True
            self.focused_widget.on_gain_focus()

    def iter_widgets(self):
        if self.layout:
            for widget in self.layout.iter_widgets():
                yield widget

    def cycle_next_focus(self, reverse=False):
        widgets = list(x for x in self.iter_widgets() if x.focusable)
        if not widgets:
            self.change_focus(None)
        elif self.focused_widget is None:
            self.change_focus(widgets[0])
        else:
            index = widgets.index(self.focused_widget)
            if index < 0:
                self.change_focus(widgets[0])
            else:
                if not reverse:
                    index = (index + 1) % len(widgets)
                else:
                    index = (index + len(widgets) - 1) % len(widgets)
                self.change_focus(widgets[index])

    def calc_maximum_size(self) -> Vec2:
        if self.layout:
            self.set_maximum_size(self.layout.calc_maximum_size())
        return self.get_maximum_size()

    def calc_minimum_size(self) -> Vec2:
        if self.layout:
            self.set_minimum_size(self.layout.calc_minimum_size())
        return self.get_minimum_size()

    def on_update(self):
        pass

    def on_draw(self, g):
        pass

    def on_gain_focus(self):
        pass

    def on_lose_focus(self):
        pass

    def set_layout(self, layout):
        self.layout = layout
        self.layout.parent = self

    def focus(self) -> bool:
        self.get_root_parent().change_focus(self)

    def is_focused(self) -> bool:
        return self.focused

    def main_update(self):
        self.calc_maximum_size()
        self.calc_minimum_size()
        self.update()

    def update(self):
        self.on_update()
        if self.layout:
            self.layout.set_rect(Rect(self.get_rect()))
            self.layout.update()

    def draw(self, g):
        if not g.is_rect_in_viewport(self.get_rect()):
            return
        
        c = color.WHITE
        if self.is_focused():
            c = color.rgb(235, 235, 255)
        g.fill_rect(self.rect, color=c)

        self.on_draw(g)
        if self.layout:
            self.layout.draw(g)

        c = color.BLACK
        if self.is_focused():
            c = color.BLUE
        g.draw_rect(self.rect, color=c)

    def _get_layout_item_children(self):
        if self.layout:
            return [self.layout]
        return []
