from enum import IntEnum
import os
import pygame
import random
import time
from cmg.color import Colors
from cmg.color import Color
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

    def __init__(self, widget=None, title=None):
        super().__init__()
        if title is None and widget:
            title = widget.get_window_title()
        self.__title = AccentedText(title)
        self.__widget = widget
        self.__cursor_item = None
        self.__cursor_pos = 0.0

    def get_widget(self) -> widgets.Widget:
        return self.__widget

    def set_widget(self, widget: widgets.Widget):
        self.__widget = widget
        
    def on_key_pressed(self, key, mod, text):
        if self.__widget:

            # Check for tab to change focus
            if key == Keys.K_TAB and mod == KeyMods.NONE:
                self.__widget.cycle_next_focus(reverse=False)
                return
            elif key == Keys.K_TAB and mod == KeyMods.LSHIFT:
                self.__widget.cycle_next_focus(reverse=True)
                return

            # Notify widgets
            widget = self.__widget.get_focused_widget()
            while widget:
                if widget.on_key_pressed(key, mod, text):
                    break
                for shortcut in widget.get_key_shortcuts():
                    if shortcut.matches(key, mod):
                        if shortcut.invoke():
                            break
                widget = widget.get_parent_widget()
        
    def on_key_released(self, key, mod):
        if self.__widget:
            # Notify widgets
            widget = self.__widget.get_focused_widget()
            while widget:
                if widget.on_key_released(key, mod):
                    break
                widget = widget.get_parent_widget()
            
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
        self.buttons[1] = Button("Menu", self.click)
        self.buttons[2] = Button("Scroll Down")

        self.__cursor_item = None
        self.__cursor_pos = 0.5
        for widget in self.__widget.iter_child_widgets():
            if widget.is_focusable():
                self.__cursor_item = widget
                break

        screen_width, screen_height = self.app.screen.get_size()
        viewport = pygame.Rect(0, self.margin_top, screen_width,
                               screen_height - self.margin_top - self.margin_bottom)
        
    def on_end(self):
        """Called when the state ends."""
        if self.__widget:
            self.__widget.on_close()
            
    def click(self):
        if not self.__cursor_item and self.__widget.get_focused_widget():
            self.__cursor_item = self.__widget.get_focused_widget()
            self.__cursor_pos = 0.5
        if self.__cursor_item:
            self.__cursor_item.on_pressed()

    def update(self, dt):
        # Update cursor movement
        if self.__cursor_item and self.__widget.get_focused_widget() is not self.__cursor_item:
            self.__cursor_item = None

        move = self.app.inputs[2].get_amount() - self.app.inputs[0].get_amount()
        speed = 20.0
        if abs(move) > 0.001:
            if self.__cursor_item is None:
                self.__cursor_pos = 0.5
            self.__cursor_pos += move * dt * speed
            self.__cursor_item = self.__widget.get_focused_widget()

        if self.__cursor_pos >= 1.0:
            self.__cursor_pos -= 1.0
            self.__cursor_item = self.__widget.cycle_next_focus(reverse=False)
        elif self.__cursor_pos < 0.0:
            self.__cursor_pos += 1.0
            self.__cursor_item = self.__widget.cycle_next_focus(reverse=True)

        # Update layout
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

        # Draw cursor
        if self.__cursor_item:
            rect = self.__cursor_item.get_rect()

            # Draw box around widget
            g.draw_rect(rect, color=Colors.RED, thickness=2)

            # Draw cursor marker 
            vertical = True
            parent = self.__get_container_layout(self.__cursor_item)
            if parent and isinstance(parent, widgets.HBoxLayout):
                vertical = False
            if vertical:
                y = rect.top + self.__cursor_pos * rect.height
                g.draw_rect(rect.left, y, rect.width, 1, color=Colors.RED)
                g.draw_rect(rect.left - 2, y - 2, 4, 4, color=Colors.RED)
                g.draw_rect(rect.right - 2, y - 2, 4, 4, color=Colors.RED)
            else:
                x = rect.left + self.__cursor_pos * rect.width
                g.draw_rect(x, rect.top, 1, rect.height, color=Colors.RED)
                g.draw_rect(x - 2, rect.top - 2, 4, 4, color=Colors.RED)
                g.draw_rect(x - 2, rect.bottom - 2, 4, 4, color=Colors.RED)

            # Highlight how much "press" is happening
            press_percent = self.app.inputs[1].get_amount()
            # if press_percent > 0.001:
            #     w = rect.width * press_percent * 0.5
            #     color = Color(255, 100, 100, 128)
            #     g.fill_rect(rect.left, rect.top, w, rect.height, color=color)
            #     g.fill_rect(rect.right - w, rect.top, w, rect.height, color=color)

        # Draw state
        State.draw(self, g)

        # Draw title
        g.draw_accented_text(32, self.margin_top / 2,
                             text=self.__title,
                             color=Config.title_color,
                             align=Align.MiddleLeft)

    def __close(self):
        if self.__widget:
            self.__widget.close()
        else:
            self.app.pop_state()

    def __get_container_layout(self, widget):
        parent = widget.get_parent()
        while parent:
            if self.__is_container_layout(parent):
                return parent
            parent = parent.get_parent()
        return widget.get_parent()

    def __is_container_layout(self, layout):
        return (isinstance(layout, widgets.Layout) and
                len([x for x in layout.iter_widgets()
                     if self.__is_valid_widget(x)]) > 1)

    def __is_valid_widget(self, widget):
        return isinstance(widget, widgets.Widget) and widget.is_focusable()

