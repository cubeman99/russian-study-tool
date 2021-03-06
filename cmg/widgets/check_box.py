import pygame
import os
import cmg
from cmg import widgets
from cmg import gui
from cmg.event import Event
from cmg.input import Keys
from cmg.input import MouseButtons


class CheckBox(widgets.Widget):
    def __init__(self, text="", checked=False):
        super().__init__()
        self.set_focusable(True)
        
        self.clicked = Event()
        self.__text = text
        self.__font = cmg.Font(32)
        self.__surface = None
        self.__checked = checked
        self.__update_size()

    def is_checked(self) -> bool:
        return self.__checked

    def get_text(self) -> str:
        return self.__text

    def set_checked(self, checked: bool):
        if checked != self.__checked:
            self.__checked = checked
            self.clicked.emit()

    def toggle(self):
        self.set_checked(not self.__checked)

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        if text != self.__text:
            self.__text = text
            self.__surface = None
            self.__update_size()

    def on_key_pressed(self, key, mod, text):
        if key in [Keys.K_RETURN, Keys.K_SPACE]:
            self.toggle()
            
    def on_mouse_pressed(self, pos, button):
        if button == MouseButtons.LEFT:
            self.toggle()

    def on_pressed(self):
        self.toggle()

    def on_draw(self, g):
        if not self.__surface:
            self.__surface = self.__font.render(
                self.__text, color=cmg.Theme.color_text)
            
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        w = 20
        h = 20
        p = 4

        if False:
            x = self.get_rect().right - p - w
            g.draw_rect(x, y, w, h, color=cmg.Theme.color_checkbox_box)
            if self.__checked:
                g.fill_rect(x + p, y + p, w - p * 2, h - p * 2,
                            color=cmg.Theme.color_checkbox_box)
            x -= p + self.__surface.get_width()
            g.draw_image(self.__surface, x, y)
        else:
            x = self.get_rect().left + p
            g.draw_rect(x, y, w, h, color=cmg.Theme.color_checkbox_box)
            if self.__checked:
                g.fill_rect(x + p, y + p, w - p * 2, h - p * 2,
                            color=cmg.Theme.color_checkbox_box)
            x += w + p
            g.draw_image(self.__surface, x, y)
            
        # Draw the box border
        if self.is_focused():
            g.draw_rect(self.rect, color=cmg.Theme.color_outline_focused)

    def __update_size(self):
        size = self.__font.measure(self.__text)
        p = 4
        self.set_minimum_height(size.y + p)
        self.set_maximum_height(size.y + p)
        self.set_minimum_width(size.x + p + 20 + p + p)

    def __repr__(self):
        """Returns a string representation of this object."""
        return "<{}({})>".format(self.__class__.__name__, repr(self.__text))


