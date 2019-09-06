import pygame
import re
import os
import traceback
import win32clipboard
import cmg
from cmg import gui
from cmg.application import Application
from cmg.input import Keys
from cmg.input import KeyMods
from cmg.event import Event
from cmg.color import Color
from cmg.color import Colors
from cmg.widgets.widget import Widget

class TextEdit(Widget):
    """
    Single-line text box for editing text.
    """

    def __init__(self,
                 text="",
                 repeat_keys_initial_ms=400,
                 repeat_keys_interval_ms=35):
        super().__init__()
        self.set_focusable(True)

        self.text_edited = Event()
        self.return_pressed = Event()

        self.__autocomplete_source = None
        self.__background_text = None
        self.__autocomplete_text = None
        self.__background_color = Colors.WHITE
        self.__background_text_color = Colors.LIGHT_GRAY
        self.__surface_background_text = pygame.Surface((1, 1))
        self.__surface_text = pygame.Surface((1, 1))
        self.__surface = pygame.Surface((1, 1))
        self.__surface.set_alpha(0)

        self.__text = text  # Inputted text
        self.__prev_state = (None, None, None)

        self.__font = gui.Font(32)
        size = self.__font.measure(self.__text)
        self.set_minimum_height(size.y + 4)
        self.set_maximum_height(size.y + 4)
        #self.set_minimum_width(size.x + 4)
        
        # Vars to make keydowns repeat after user pressed a key for some time:
        # {event.key: (counter_int, event.unicode)} (look for "***")
        self.keyrepeat_counters = {}
        self.keyrepeat_intial_interval_ms = repeat_keys_initial_ms
        self.keyrepeat_interval_ms = repeat_keys_interval_ms

        # cursor state
        self.__select_position = None
        self.__cursor_position = len(text)  # Inside text
        self.cursor_visible = False
        self.cursor_switch_ms = 500  # /|\
        self.cursor_ms_counter = 0
        self.clock = pygame.time.Clock()

    def set_background_text(self, text: str):
        """Sets the background text of the text box."""
        self.__background_text = text

    def set_autocomplete_source(self, autocomplete_source):
        """Sets the list of autocomplete items."""
        self.__autocomplete_source = autocomplete_source
    
    def set_background_color(self, color: Color):
        """Sets the background color of the text box."""
        self.__background_color = Color(color)

    def on_lose_focus(self):
        """Called when the widget loses focus."""
        self.stop_selecting()
        self.__apply_autocomplete()

    def get_text(self) -> str:
        """Gets the text in the text box."""
        return self.__text

    def set_text(self, text: str) -> str:
        """Sets the text in the text box."""
        assert isinstance(text, str)
        self.__text = text
        self.__cursor_position = len(self.__text)

    def update(self):
        """Updates the text box."""
        if self.is_focused():

            # Update key counters:
            repeat_dict = [key for key in self.keyrepeat_counters]
            for key in repeat_dict:
                # Update clock
                self.keyrepeat_counters[key][0] += self.clock.get_time()

                # Generate new key events if enough time has passed:
                if self.keyrepeat_counters[key][0] >= self.keyrepeat_intial_interval_ms:
                    self.keyrepeat_counters[key][0] = (
                        self.keyrepeat_intial_interval_ms
                        - self.keyrepeat_interval_ms
                    )

                    # FIXME: better way to get this
                    mods = KeyMods(pygame.key.get_mods())
                    if mods == self.keyrepeat_counters[key][2]:
                        event_key, event_unicode = key, self.keyrepeat_counters[key][1]
                        self.on_key_pressed(event_key, mods, event_unicode)
                    else:
                        del self.keyrepeat_counters[key]

            # Update cursor visibility
            self.cursor_ms_counter += self.clock.get_time()
            if self.cursor_ms_counter >= self.cursor_switch_ms:
                self.cursor_ms_counter %= self.cursor_switch_ms
                self.cursor_visible = not self.cursor_visible
        else:
            self.keyrepeat_counters = {}
            self.cursor_visible = False

        # Update auto-complete
        if self.__autocomplete_source:
            self.__background_text = None
            self.__autocomplete_text = None
            if self.__text:
                for item in self.__autocomplete_source:
                    item = str(item)
                    if item.lower().startswith(self.__text.lower()):
                        self.__background_text = self.__text + item[len(self.__text):]
                        self.__autocomplete_text = item
                        if item.lower() == self.__text.lower():
                            break

        # Re-render text surface
        state = (self.__text,
                 self.__cursor_position,
                 self.__background_text)
        if state[0] != self.__prev_state[0]:
            self.text_edited.emit()
        if state[:2] != self.__prev_state[:2]:
            self.cursor_ms_counter = 0
            self.cursor_visible = self.is_focused()
        if state != self.__prev_state:
            self.__prev_state = state
            self.__surface_text = self.__font.render(self.__text)
            if self.__background_text:
                self.__surface_background_text = self.__font.render(
                    self.__background_text,
                    color=self.__background_text_color)

        self.clock.tick()

    def on_key_pressed(self, key, mod, text):
        """Called when a key is pressed."""
        if key in [Keys.K_ESCAPE, Keys.K_TAB]:
            return
        
        # Enter applies autocompletion
        if key == Keys.K_RETURN:
            self.__apply_autocomplete()
            self.return_pressed.emit()
            return

        # If none exist, create counter for that key:
        if key not in self.keyrepeat_counters:
            self.keyrepeat_counters[key] = [0, text, mod]

        if KeyMods.LSHIFT in mod and KeyMods.LCTRL in mod:
            if key == Keys.K_INSERT:
                self.paste()

        elif KeyMods.LCTRL in mod:
            if key == Keys.K_V:
                self.paste()
            if key == Keys.K_X:
                self.cut()
            if key == Keys.K_C:
                self.copy()
            if key == Keys.K_A:
                self.select_all()
            if key == Keys.K_INSERT:
                self.copy()

        elif key == Keys.K_BACKSPACE:
            if self.is_selecting():
                self.delete_selection()
            else:
                self.__text = (self.__text[:max(self.__cursor_position - 1, 0)] +
                               self.__text[self.__cursor_position:])
            self.__cursor_position = max(self.__cursor_position - 1, 0)
        elif key == Keys.K_DELETE:
            if self.is_selecting():
                self.delete_selection()
            else:
                self.__text = (self.__text[:self.__cursor_position] +
                               self.__text[self.__cursor_position + 1:])
        elif key == Keys.K_RIGHT:
            if KeyMods.LSHIFT in mod:
                self.start_selection()
            else:
                self.stop_selecting()
            self.__cursor_position = min(
                self.__cursor_position + 1, len(self.__text))
        elif key == Keys.K_LEFT:
            if KeyMods.LSHIFT in mod:
                self.start_selection()
            else:
                self.stop_selecting()
            self.__cursor_position = max(self.__cursor_position - 1, 0)
        elif key == Keys.K_END:
            if KeyMods.LSHIFT in mod:
                self.start_selection()
            else:
                self.stop_selecting()
            self.__cursor_position = len(self.__text)
        elif key == Keys.K_HOME:
            if KeyMods.LSHIFT in mod:
                self.start_selection()
            else:
                self.stop_selecting()
            self.__cursor_position = 0
        elif len(text) > 0:
            self.delete_selection()
            self.insert_text(text)

    def on_key_released(self, key, mod):
        """Called when a key is released."""
        if key in self.keyrepeat_counters:
            del self.keyrepeat_counters[key]

    def insert_text(self, text: str):
        """Insert text at the current cursor position."""
        self.__text = (
            self.__text[:self.__cursor_position] + text +
            self.__text[self.__cursor_position:])
        self.__cursor_position += len(text)

    def get_selection_text(self) -> str:
        """Returns the string of selected texet."""
        if self.__select_position is None:
            return None
        start = min(self.__select_position, self.__cursor_position)
        end = max(self.__select_position, self.__cursor_position)
        return self.__text[start:end]

    def is_selecting(self) -> bool:
        """Returns True if currently selecting text."""
        return (self.__select_position is not None and
                self.__select_position != self.__cursor_position)

    def start_selection(self):
        """Begin selecting at the current cursor position."""
        if self.__select_position is None:
            self.__select_position = self.__cursor_position

    def delete_selection(self):
        """Delete selected text."""
        if self.is_selecting():
            start = min(self.__select_position, self.__cursor_position)
            end = max(self.__select_position, self.__cursor_position)
            self.__text = self.__text[:start] + self.__text[end:]
            self.__cursor_position = start
        self.__select_position = None

    def stop_selecting(self) -> bool:
        """Deselect if selecting."""
        self.__select_position = None

    def select_all(self):
        """Select all text."""
        if self.__text:
            self.__select_position = 0
            self.__cursor_position = len(self.__text)
        else:
            self.__select_position = None
    
    def copy(self):
        """Copy text in selection."""
        text = self.get_selection_text()
        if text:
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
    
    def cut(self):
        """Copy and delete text in selection."""
        self.copy()
        self.delete_selection()

    def paste(self):
        """Insert text from clipboard."""
        try:
            text = None
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            if text:
                self.delete_selection()
                self.insert_text(text)
        except Exception:
            traceback.print_exc()

    def on_draw(self, g):
        """Draw the text box."""
        top_padding = int((self.get_height() - self.__surface_text.get_height()) / 2)
        left_padding = 4

        g.fill_rect(self.rect, color=self.__background_color)

        if self.__background_text:
            g.draw_image(self.__surface_background_text,
                         self.rect.left + left_padding,
                         self.rect.top + top_padding)

        if self.is_selecting():
            cursor_height = self.__surface_text.get_height()
            start = min(self.__select_position, self.__cursor_position)
            end = max(self.__select_position, self.__cursor_position)
            box_offset = self.__font.measure(self.__text[:start])[0]
            box_offset += self.rect.left + left_padding
            box_span = self.__font.measure(self.__text[start:end])[0]
            g.fill_rect(box_offset, self.rect.top + top_padding,
                        box_span, cursor_height,
                        color=Colors.BLUE)
        if self.__text:
            g.draw_image(self.__surface_text,
                         self.rect.left + left_padding,
                         self.rect.top + top_padding)

        # Draw the cursor
        if self.cursor_visible:
            cursor_height = self.__surface_text.get_height()
            cursor_width = int(cursor_height / 20 + 1)
            cursor_x_pos = self.rect.left + left_padding + self.__font.measure(
                self.__text[:self.__cursor_position])[0]
            g.fill_rect(cursor_x_pos, self.rect.top + top_padding,
                        cursor_width, cursor_height,
                        color=self.__font.get_text_color())

    def __get_ctrl_boundary(self, step=1):
        """
        Returns the next character index along word boundaries.
        Used for when holding control and pressing left/right/backspace/delete
        """
        pos = self.__cursor_position
        while pos > 0 and pos < len(self.__text):
            if not re.match(r"[A-Za-z0-9]", self.__text[pos]):
                break
            pos += step
        return pos

    def __apply_autocomplete(self):
        """Loads the current autocomplete suggestion text into the text box."""
        if self.__autocomplete_source and self.__background_text:
            self.set_text(self.__autocomplete_text)
