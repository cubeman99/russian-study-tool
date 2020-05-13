import pygame
import os
import cmg
from cmg import widgets
from cmg import gui


class GroupBox(widgets.Widget):
    def __init__(self, text="", layout: widgets.Layout=None):
        super().__init__()
        if layout:
            self.set_layout(layout)
        self.__text = text
        self.__font = cmg.Font(32)
        self.__surface = None
        self.__border_inside_margin = self.__font.get_size() // 2
        self.__border_outside_margin = self.__border_inside_margin
        self.__update_size()

    def get_text(self) -> str:
        return self.__text

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        if text != self.__text:
            self.__text = text
            self.__surface = None
            self.__update_size()
            
    def calc_maximum_size(self) -> cmg.Vec2:
        bx = 2 * (self.__border_outside_margin + self.__border_inside_margin)
        max_size = cmg.Vec2(bx, bx)
        if self.layout:
            max_size += self.layout.calc_maximum_size()
        else:
            max_size += cmg.Vec2(self.DEFAULT_DEFAULT_MAX_SIZE, self.DEFAULT_DEFAULT_MAX_SIZE)
        self.set_maximum_size(max_size)
        return self.get_maximum_size()

    def calc_minimum_size(self) -> cmg.Vec2:
        bx = 2 * (self.__border_outside_margin + self.__border_inside_margin)
        min_size = cmg.Vec2(bx, bx)
        if self.layout:
            min_size += self.layout.calc_minimum_size()
        self.set_minimum_size(min_size)
        return self.get_minimum_size()

    def update_layout(self):
        if self.layout:
            rect = cmg.Rect(self.get_rect())
            bx = self.__border_outside_margin + self.__border_inside_margin
            rect.inflate_ip(-bx * 2, -bx * 2)
            self.layout.set_rect(rect)
            self.layout.update()

    def on_draw(self, g: cmg.Graphics):
        # Render the text
        if not self.__surface:
            self.__surface = self.__font.render(
                self.__text, color=cmg.Theme.color_text)

        # Draw border lines
        margin = 4
        b1 = self.__border_inside_margin
        rect = self.get_rect().inflate(-b1 * 2, -b1 * 2)
        g.draw_rect(rect, color=cmg.Theme.color_outline, thickness=2)

        # Draw title
        x = self.rect.left + self.__border_outside_margin + self.__border_inside_margin
        y = self.rect.top
        g.fill_rect(x - 2, y,
                    self.__surface.get_width() + 4,
                    self.__surface.get_height(),
                    color=cmg.Theme.color_background)
        g.draw_image(self.__surface, x, y)

    def __update_size(self):
        size = self.__font.measure(self.__text)
        self.__border_inside_margin = size.y // 2
        self.__border_outside_margin = self.__border_inside_margin
        self.set_minimum_height(size.y + 4)
        self.set_maximum_height(size.y + 4)
        self.set_minimum_width(size.x + 4)

    def __repr__(self):
        """Returns a string representation of this object."""
        return "<{}({})>".format(self.__class__.__name__, repr(self.__text))
