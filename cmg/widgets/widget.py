import traceback
from pygame.rect import Rect
from cmg.graphics import Graphics
from cmg import color
from cmg.widgets.layout_item import LayoutItem
from cmg.math import Vec2
from cmg.event import Event
from cmg.input import KeyShortcut


class Widget(LayoutItem):
    def __init__(self):
        super().__init__()
        self.layout = None
        self.rect = Rect(80, 200, 200, 60)
        self.focused_widget = None
        self.focused = False
        self.focusable = False
        self.__window_title = ""
        self.__enabled = True
        self.__visible = True
        self.__key_shortcuts = []

        # Events
        self.closed = Event()
        self.focus_lost = Event()
        self.focus_gained = Event()

    def is_focusable(self) -> bool:
        return self.focusable
    
    def is_enabled(self) -> bool:
        return self.__enabled

    def get_layout(self):
        return self.layout
    
    def is_visible(self) -> bool:
        """Returns True if this widget is visible."""
        return self.__visible

    def get_focused_widget(self):
        return self.focused_widget

    def get_window_title(self) -> str:
        return self.__window_title

    def get_key_shortcuts(self) -> list:
        return self.__key_shortcuts

    def get_parent_widget(self):
        parent = self.get_parent()
        while parent:
            if isinstance(parent, Widget):
                return parent
            parent = parent.get_parent()
        return None

    def set_window_title(self, window_title: str):
        self.__window_title = window_title

    def set_visible(self, visible: bool):
        if not visible:
            self.closed.emit()
        self.__visible = visible

    def add_key_shortcut(self, shortcut: str, callback=None):
        shortcut = KeyShortcut(shortcut, callback=callback)
        self.__key_shortcuts.append(shortcut)
        return shortcut

    def set_parent(self, parent):
        if parent != self.parent:
            if self.focused:
                self.get_root_parent().cycle_next_focus()
            if self.focused:
                self.get_root_parent().change_focus(None)
            self.parent = parent
    
    def show(self):
        self.set_visible(True)

    def close(self):
        self.set_visible(False)

    def set_focusable(self, focusable: bool):
        self.focusable = focusable

    def set_enabled(self, enabled: bool):
        self.__enabled = enabled

    def change_focus(self, widget):
        if self.focused_widget:
            self.focused_widget.focused = False
            self.focused_widget.on_lose_focus()
            self.focused_widget.focus_lost.emit()
        self.focused_widget = widget
        if self.focused_widget:
            self.focused_widget.focused = True
            self.focused_widget.on_gain_focus()
            self.focused_widget.focus_gained.emit()

    def iter_widgets(self):
        if self.layout:
            for widget in self.layout.iter_widgets():
                yield widget

    def cycle_next_focus(self, reverse=False):
        widgets = list(x for x in self.iter_widgets()
                       if x.is_focusable() and x.is_enabled())
        if not widgets:
            self.change_focus(None)
        elif self.focused_widget is None or self.focused_widget not in widgets:
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
        return self.focused_widget

    def calc_maximum_size(self) -> Vec2:
        if self.layout:
            self.set_maximum_size(self.layout.calc_maximum_size())
        return self.get_maximum_size()

    def calc_minimum_size(self) -> Vec2:
        if self.layout:
            self.set_minimum_size(self.layout.calc_minimum_size())
        return self.get_minimum_size()

    def on_close(self):
        """Called when the widget is closed."""
        pass

    def on_update(self):
        pass

    def on_draw(self, g):
        pass

    def on_gain_focus(self):
        pass

    def on_lose_focus(self):
        pass
    
    def on_key_pressed(self, key, mod, text):
        return False
    
    def on_key_released(self, key, mod):
        return False
    
    def on_mouse_pressed(self, pos, button):
        return False

    def on_mouse_released(self, pos, button):
        return False

    def on_pressed(self):
        return False

    def set_layout(self, layout):
        self.layout = layout
        self.layout.set_parent(self)

    def focus(self) -> bool:
        self.get_root_parent().change_focus(self)

    def is_focused(self) -> bool:
        return self.focused

    def iter_child_widgets(self):
        yield self
        if self.layout:
            for widget in self.layout.iter_child_widgets():
                yield widget

    def main_update(self):
        self.calc_maximum_size()
        self.calc_minimum_size()
        self.update()

        # try:
        #     log = ""
        #     for child in self.iter_child_widgets():
        #         log += repr(child) + ", " + repr(child.get_rect()) + "\n"
        #         if child.get_width() < 0 or child.get_height() < 0:
        #             raise Exception(child)
        # except:
        #     print(log)
        #     traceback.print_exc()

    def update(self):
        self.on_update()
        self.update_layout()

    def update_layout(self):
        if self.layout:
            self.layout.set_rect(Rect(self.get_rect()))
            self.layout.update()

    def draw(self, g):
        if not g.is_rect_in_viewport(self.get_rect()):
            return
        if self.rect.width <= 0 or self.rect.height <= 0:
            return
        
        c = color.WHITE
        if self.is_focused():
            c = color.rgb(235, 235, 255)
            g.fill_rect(self.rect, color=c)

        self.on_draw(g)
        if self.layout:
            self.layout.draw(g)

        if not self.is_enabled():
            g.fill_rect(self.rect, color=color.rgba(255, 255, 255, 128))

    def _get_layout_item_children(self):
        if self.layout:
            return [self.layout]
        return []
