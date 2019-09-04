import pygame
import os
from cmg import widgets
from cmg.graphics import Graphics
from cmg.math import Vec2
from cmg import color
from cmg.input import MouseButtons, KeyMods, Keys
from cmg.widgets import widget
from cmg.widgets.layout import HBoxLayout


class SubRegionLayout(widgets.Layout):
    def __init__(self, widget=None):
        super().__init__()
        self.__widget = widget
        self.__surface = None
        self.__offset = Vec2(0, 0)

    def get_offset(self) -> Vec2:
        return self.__offset

    def get_widget(self) -> widgets.Widget:
        return self.__widget

    def set_offset(self, offset: Vec2):
        self.__offset = Vec2(offset)

    def set_widget(self, widget: widgets.Widget):
        assert isinstance(widget, widgets.Widget)
        self.__widget = widget
        if widget:
            widget.set_parent(self)

    def get_children(self):
        return (self.__widget,)

    def on_update(self):
        if self.__widget:
            self.__widget.set_rect(self.get_rect())
            size = Vec2(self.get_size())
            size.y = self.__widget.get_minimum_height()
            self.__widget.set_size(size)

    def calc_maximum_size(self):
        if self.__widget:
            self.__widget.calc_maximum_size()
        return self.get_maximum_size()

    def calc_minimum_size(self):
        if self.__widget:
            self.__widget.calc_minimum_size()
        return self.get_minimum_size()

    def draw_children(self, g):
        if self.__widget:
            if not self.__surface or self.__surface.get_size() != self.rect.size:
                self.__surface = pygame.Surface(self.rect.size)

            # Render the widget into the sub-surface
            subg = Graphics(self.__surface)
            subg.clear(color.WHITE)
            subg.set_translation(-(self.rect.left + self.__offset[0]),
                                 -(self.rect.top + self.__offset[1]))
            self.__widget.draw(subg)
            g.draw_image(self.__surface, self.rect.topleft)


class ScrollBar(widgets.Widget):
    def __init__(self, axis=1):
        super().__init__()

        self.__value = 0
        self.__minimum = 0
        self.__maximum = 100
        self.__page_step = 1
        self.__axis = axis
        self.__end_size = 20

        if self.__axis == 1:
            self.set_maximum_width(self.__end_size)
        else:
            self.set_maximum_height(self.__end_size)

    def get_value(self):
        return self.__value

    def get_page_step(self):
        return self.__page_step

    def set_minimum(self, minimum):
        self.__minimum = minimum

    def set_maximum(self, maximum):
        self.__maximum = maximum

    def set_range(self, minimum, maximum):
        self.__minimum = minimum
        self.__maximum = maximum

    def set_value(self, value):
        self.__value = max(self.__minimum, min(self.__maximum, value))

    def set_page_step(self, page_step):
        self.__page_step = page_step

    def draw(self, g):
        axis = self.__axis
        end_size = Vec2(self.__end_size, self.__end_size)


        topleft = Vec2(self.get_rect().topleft)
        size = self.get_size()
        end_size[1 - axis] = size[1 - axis]
        bar_size = Vec2(size)
        bar_pos = Vec2(topleft)
        bar_pos[axis] += end_size[axis]
        span_size = size[axis] - (end_size[axis] * 2)
        bar_size[axis] = span_size
        if self.__maximum > self.__minimum:
            percent = ((self.__value - self.__minimum) /
                       (self.__maximum - self.__minimum))
            bar_size[axis] = int(
                (span_size * self.__page_step) /
                (self.__maximum - self.__minimum + self.__page_step))
            bar_pos[axis] += int(round((span_size - bar_size[axis]) * percent))

        xy = Vec2(topleft)
        end_rect_1 = pygame.Rect(xy.totuple(), end_size.totuple())
        xy[axis] += end_size[axis]

        bar_rect = pygame.Rect(bar_pos.totuple(), bar_size.totuple())

        xy[axis] = topleft[axis] + size[axis] - end_size[axis]
        end_rect_2 = pygame.Rect(xy.totuple(), end_size.totuple())

        g.fill_rect(self.get_rect(), color=color.LIGHT_GRAY)

        g.fill_rect(end_rect_1, color=color.YELLOW)
        g.draw_rect(end_rect_1, color=color.BLACK)

        g.fill_rect(end_rect_2, color=color.GREEN)
        g.draw_rect(end_rect_2, color=color.BLACK)

        g.fill_rect(bar_rect, color=color.WHITE)
        g.draw_rect(bar_rect, color=color.BLACK)


class AbstractScrollArea(widgets.Widget):
    def __init__(self, widget=None):
        super().__init__()
        self.__widget = None
        self.__layout = SubRegionLayout()
        self.__scrollbar_h = ScrollBar(axis=1)

        main_layout = HBoxLayout()
        main_layout.add_layout(self.__layout)
        main_layout.add_widget(self.__scrollbar_h)
        self.set_layout(main_layout)

        if widget:
            self.set_widget(widget)

    def get_widget(self) -> widgets.Widget:
        return self.__widget

    def set_widget(self, widget: widgets.Widget):
        assert isinstance(widget, widgets.Widget)
        self.__layout.set_widget(widget)
        self.__widget = widget

    def on_update(self):
        viewport_height = self.__layout.get_height()
        area_height = self.__widget.get_height()
        self.__scrollbar_h.set_minimum(0)
        self.__scrollbar_h.set_maximum(
            max(0, area_height - viewport_height))
        self.__scrollbar_h.set_page_step(area_height)
        self.__layout.set_offset(Vec2(
            0, self.__scrollbar_h.get_value()))

    def on_key_pressed(self, key, mod, text):
        if mod == KeyMods.NONE:
            if key == MouseButtons.PAGE_UP:
                self.__scrollbar_h.set_value(self.__scrollbar_h.get_value() -
                                             self.__scrollbar_h.get_page_step())
            elif key == MouseButtons.PAGE_DOWN:
                self.__scrollbar_h.set_value(self.__scrollbar_h.get_value() +
                                             self.__scrollbar_h.get_page_step())
            
    def on_mouse_pressed(self, pos, button):
        scroll = 0
        if button == MouseButtons.WHEEL_UP:
            scroll = -1
        elif button == MouseButtons.WHEEL_DOWN:
            scroll = 1
        if scroll != 0:
            self.__scrollbar_h.set_value(
                self.__scrollbar_h.get_value() + (scroll * 40))

    def on_mouse_released(self, pos, button):
        pass