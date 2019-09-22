from enum import IntEnum
import os
import pygame
import random
import time
from cmg import color
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import Card
from study_tool.card_set import *
from study_tool.entities.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.card_database import CardDatabase
from cmg.widgets.text_edit import TextEdit
from cmg.application import Application
from cmg.input import Keys
from cmg import widgets
from study_tool import card

class GUIState(State):

    def __init__(self, widget=None, title="Untitled GUI"):
        super().__init__()
        self.__title = title
        self.__widget = widget

    def get_widget(self) -> widgets.Widget:
        return self.__widget

    def set_widget(self, widget: widgets.Widget):
        self.__widget = widget
        
    def on_key_pressed(self, key, mod, text):
        if self.__widget:
            if key == Keys.K_TAB:
                if KeyMods.LSHIFT in mod:
                    self.__widget.cycle_next_focus(reverse=True)
                else:
                    self.__widget.cycle_next_focus(reverse=False)
            if self.__widget.get_focused_widget():
                self.__widget.get_focused_widget().on_key_pressed(key, mod, text)
        
    def on_key_released(self, key, mod):
        if self.__widget and self.__widget.get_focused_widget():
            self.__widget.get_focused_widget().on_key_released(key, mod)
            
    def on_mouse_pressed(self, pos, button):
        if self.__widget:
            widget = self.get_widget_at_point(self.__widget, pos)
            if widget and widget.is_enabled():
                if widget.is_focusable() and button in [MouseButtons.LEFT, MouseButtons.RIGHT]:
                    widget.focus()
            for widget in self.iter_widgets_at_point(self.__widget, pos):
                if widget.is_enabled():
                    widget.on_mouse_pressed(pos, button)

    def on_mouse_released(self, pos, button):
        if self.__widget:
            widget = self.get_widget_at_point(self.__widget, pos)
            if widget and widget.is_enabled():
               widget.on_mouse_released(pos, button)

    def get_widget_at_point(self, item, pos):
        layout = item
        if isinstance(item, widgets.Widget):
            layout = item.get_layout()
        rect = item.get_rect()
        if (pos.x >= rect.left and pos.y >= rect.top and
            pos.x < rect.right and pos.y < rect.bottom):
            if layout:
                pos += layout.get_offset()
                for child in layout.get_children():
                    result = self.get_widget_at_point(child, pos)
                    if result:
                        return result
            elif isinstance(item, widgets.Widget):
                return item
        return None

    def iter_widgets_at_point(self, item, pos):
        layout = item
        if isinstance(item, widgets.Widget):
            layout = item.get_layout()
        rect = item.get_rect()
        if pos.x >= rect.left and pos.y >= rect.top and pos.x < rect.right and pos.y < rect.bottom:
            if isinstance(item, widgets.Widget):
                yield item
            if layout:
                pos += layout.get_offset()
                for child in layout.get_children():
                    for subitem in self.iter_widgets_at_point(child, pos):
                        yield subitem


    def begin(self):
        self.buttons[0] = Button("Scroll Up")
        self.buttons[1] = Button("Menu", self.pause)
        self.buttons[2] = Button("Scroll Down")

        screen_width, screen_height = self.app.screen.get_size()
        viewport = pygame.Rect(0, self.margin_top, screen_width,
                               screen_height - self.margin_top - self.margin_bottom)
        
    def on_end(self):
        """Called when the state ends."""
        if self.__widget:
            self.__widget.on_close()

    def pause(self):
        self.app.push_state(SubMenuState("Pause",
                                         [("Resume", None),
                                          ("Menu", self.__close),
                                          ("Exit", self.app.quit)]))

    def update(self, dt):
        if self.__widget:
            screen_width, screen_height = self.app.screen.get_size()
            self.__widget.rect.top = self.margin_top + 4
            self.__widget.rect.left = 4
            self.__widget.rect.width = screen_width - 8
            self.__widget.rect.height = screen_height - self.margin_top - self.margin_bottom - 8
            self.__widget.main_update()
            if not self.__widget.is_visible():
                self.app.pop_state()

    def draw(self, g):
        # Draw the widget
        if self.__widget:
            self.__widget.draw(g)

        # Draw state
        State.draw(self, g)

        # Draw title
        g.draw_text(32, self.margin_top / 2,
                    text=self.__title,
                    color=Config.title_color,
                    align=Align.MiddleLeft)

    def __close(self):
        if self.__widget:
            self.__widget.close()
        else:
            self.app.pop_state()
