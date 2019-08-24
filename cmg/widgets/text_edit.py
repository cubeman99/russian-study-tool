import pygame
import re
import os
from cmg.application import Application
from cmg.input import Keys
from cmg.event import Event
from cmg.widgets.widget import Widget


class TextEdit(Widget):
    def __init__(self,
                 text="",
                 font_family="",
                 font_size=35,
                 antialias=True,
                 text_color=(0, 0, 0),
                 cursor_color=(0, 0, 1),
                 repeat_keys_initial_ms=400,
                 repeat_keys_interval_ms=35):
        super().__init__()
        self.set_focusable(True)
        height = font_size + 4
        self.set_minimum_height(height)
        self.set_maximum_height(height)

        self.text_edited = Event()
        self.return_pressed = Event()

        self.__autocomplete_source = None
        self.__background_text = None
        self.__autocomplete_text = None
        self.__background_text_color = (192, 192, 192)
        self.__surface_background_text = pygame.Surface((1, 1))
        self.__surface_text = pygame.Surface((1, 1))
        self.__surface = pygame.Surface((1, 1))
        self.__surface.set_alpha(0)

        self.antialias = antialias
        self.text_color = text_color
        self.font_size = font_size
        self.__text = text  # Inputted text
        self.__prev_state = (None, None, None)

        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)

        self.cursor_position = 0
        self.keyrepeat_counters = {}

        # Text-surface will be created during the first update call:
        self.font_object = pygame.font.Font(None, 30)

        # Vars to make keydowns repeat after user pressed a key for some time:
        # {event.key: (counter_int, event.unicode)} (look for "***")
        self.keyrepeat_counters = {}
        self.keyrepeat_intial_interval_ms = repeat_keys_initial_ms
        self.keyrepeat_interval_ms = repeat_keys_interval_ms

        # Things cursor:
        self.cursor_surface = pygame.Surface(
            (int(self.font_size / 20 + 1), self.font_size))
        self.cursor_surface.fill(cursor_color)
        self.cursor_position = len(text)  # Inside text
        self.cursor_visible = False
        self.cursor_switch_ms = 500  # /|\
        self.cursor_ms_counter = 0
        self.clock = pygame.time.Clock()

    def set_autocomplete_source(self, autocomplete_source):
        self.__autocomplete_source = autocomplete_source

    def on_lose_focus(self):
        self.__apply_autocomplete()

    def get_text(self) -> str:
        return self.__text

    def set_text(self, text: str) -> str:
        assert isinstance(text, str)
        self.__text = text
        self.cursor_position = len(self.__text)

    def text(self) -> str:
        return self.__text

    def update(self):
        if self.is_focused():

            # Update key counters:
            for key in self.keyrepeat_counters:
                # Update clock
                self.keyrepeat_counters[key][0] += self.clock.get_time()

                # Generate new key events if enough time has passed:
                if self.keyrepeat_counters[key][0] >= self.keyrepeat_intial_interval_ms:
                    self.keyrepeat_counters[key][0] = (
                        self.keyrepeat_intial_interval_ms
                        - self.keyrepeat_interval_ms
                    )

                    event_key, event_unicode = key, self.keyrepeat_counters[key][1]
                    self.on_key_pressed(event_key, event_unicode)

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
                 self.cursor_position,
                 self.__background_text)
        if state[0] != self.__prev_state[0]:
            self.text_edited.emit()
        if state[:2] != self.__prev_state[:2]:
            self.cursor_ms_counter = 0
            self.cursor_visible = self.is_focused()
        if state != self.__prev_state:
            self.__prev_state = state
            self.__surface_text = self.font_object.render(
                self.__text,
                self.antialias,
                self.text_color)
            if self.__background_text:
                self.__surface_background_text = self.font_object.render(
                    self.__background_text,
                    self.antialias,
                    self.__background_text_color)

        self.clock.tick()

    def on_key_pressed(self, key, text):
        if key in [Keys.K_ESCAPE, Keys.K_TAB]:
            return
        
        # Enter applies autocompletion
        if key == Keys.K_RETURN:
            self.__apply_autocomplete()
            self.return_pressed.emit()
            return

        # If none exist, create counter for that key:
        if key not in self.keyrepeat_counters:
            self.keyrepeat_counters[key] = [0, text]

        if key == Keys.K_BACKSPACE:
            self.__text = (
                self.__text[:max(self.cursor_position - 1, 0)] +
                self.__text[self.cursor_position:]
            )
            self.cursor_position = max(self.cursor_position - 1, 0)
        elif key == Keys.K_DELETE:
            self.__text = (
                self.__text[:self.cursor_position] +
                self.__text[self.cursor_position + 1:]
            )
        elif key == Keys.K_RIGHT:
            self.cursor_position = min(
                self.cursor_position + 1, len(self.__text))
        elif key == Keys.K_LEFT:
            self.cursor_position = max(self.cursor_position - 1, 0)
        elif key == Keys.K_END:
            self.cursor_position = len(self.__text)
        elif key == Keys.K_HOME:
            self.cursor_position = 0
        else:
            self.__text = (
                self.__text[:self.cursor_position] + text +
                self.__text[self.cursor_position:]
            )
            self.cursor_position += len(text)

    def on_key_released(self, key):
        # If none exist, create counter for that key:
        if key in self.keyrepeat_counters:
            del self.keyrepeat_counters[key]

    def on_draw(self, g):
        y = self.rect.top + \
            int((self.get_height() - self.__surface.get_height()) / 2)
        if self.__background_text:
            g.draw_image(self.__surface_background_text, self.rect.left + 4, y)
        if self.__text:
            g.draw_image(self.__surface_text, self.rect.left + 4, y)
        if self.cursor_visible:
            cursor_y_pos = self.font_object.size(
                self.__text[:self.cursor_position])[0]
            if self.cursor_position > 0:
                cursor_y_pos -= self.cursor_surface.get_width()
            g.draw_image(self.cursor_surface, (cursor_y_pos, 0))

    def __get_ctrl_boundary(self, step=1):
        pos = self.cursor_position
        while pos > 0 and pos < len(self.__text):
            if not re.match(r"[A-Za-z0-9]", self.__text[pos]):
                break
            pos += step
        return pos

    def __apply_autocomplete(self):
        if self.__autocomplete_source and self.__background_text:
            self.set_text(self.__autocomplete_text)
