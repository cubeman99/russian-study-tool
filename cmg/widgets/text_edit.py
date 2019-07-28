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

        self.text_edited = Event()

        self.antialias = antialias
        self.text_color = text_color
        self.font_size = font_size
        self.input_string = text  # Inputted text
        self.__prev_state = (None, None, None)

        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)

        self.cursor_position = 0
        self.keyrepeat_counters = {}

        # Text-surface will be created during the first update call:
        self.font_object = pygame.font.Font(None, 30)
        self.surface = pygame.Surface((1, 1))
        self.surface.set_alpha(0)

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
        self.cursor_visible = True  # Switches every self.cursor_switch_ms ms
        self.cursor_switch_ms = 500  # /|\
        self.cursor_ms_counter = 0
        self.clock = pygame.time.Clock()

        Application.instance.input.key_pressed.connect(
            self.on_key_press)
        Application.instance.input.key_released.connect(
            self.on_key_release)

    def text(self) -> str:
        return self.input_string

    def update(self):
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
                self.on_key_press(event_key, event_unicode)

        # Update cursor visibility
        self.cursor_ms_counter += self.clock.get_time()
        if self.cursor_ms_counter >= self.cursor_switch_ms:
            self.cursor_ms_counter %= self.cursor_switch_ms
            self.cursor_visible = not self.cursor_visible

        # Re-render text surface
        state = (self.input_string, self.cursor_position, self.cursor_visible)
        if state[0] != self.__prev_state[0]:
            self.text_edited.emit()
        if state[:2] != self.__prev_state[:2]:
            self.cursor_ms_counter = 0
            self.cursor_visible = True
        if state != self.__prev_state:
            self.__prev_state = state
            self.surface = self.font_object.render(
                self.input_string, self.antialias, self.text_color)

            if self.cursor_visible:
                cursor_y_pos = self.font_object.size(
                    self.input_string[:self.cursor_position])[0]
                # Without this, the cursor is invisible when
                # self.cursor_position > 0:
                if self.cursor_position > 0:
                    cursor_y_pos -= self.cursor_surface.get_width()
                self.surface.blit(self.cursor_surface, (cursor_y_pos, 0))

        self.clock.tick()

    def on_key_press(self, key, text):
        # If none exist, create counter for that key:
        if key not in self.keyrepeat_counters:
            self.keyrepeat_counters[key] = [0, text]

        if key == Keys.K_BACKSPACE:
            self.input_string = (
                self.input_string[:max(self.cursor_position - 1, 0)] +
                self.input_string[self.cursor_position:]
            )
            self.cursor_position = max(self.cursor_position - 1, 0)
        elif key == Keys.K_DELETE:
            self.input_string = (
                self.input_string[:self.cursor_position] +
                self.input_string[self.cursor_position + 1:]
            )
        elif key == Keys.K_RIGHT:
            self.cursor_position = min(
                self.cursor_position + 1, len(self.input_string))
        elif key == Keys.K_LEFT:
            self.cursor_position = max(self.cursor_position - 1, 0)
        elif key == Keys.K_END:
            self.cursor_position = len(self.input_string)
        elif key == Keys.K_HOME:
            self.cursor_position = 0
        else:
            self.input_string = (
                self.input_string[:self.cursor_position] + text +
                self.input_string[self.cursor_position:]
            )
            self.cursor_position += len(text)

    def on_key_release(self, key):
        # If none exist, create counter for that key:
        if key in self.keyrepeat_counters:
            del self.keyrepeat_counters[key]

    def __get_ctrl_boundary(self, step=1):
        pos = self.cursor_position
        while pos > 0 and pos < len(self.input_string):
            if not re.match(r"[A-Za-z0-9]", self.input_string[pos]):
                break
            pos += step
        return pos
