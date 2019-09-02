import pygame
import time
from cmg import color
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_tool.config import Config


class Button:
    def __init__(self, name, action=lambda: None, hold_time=0):
        self.name = name
        self.action = action
        self.hold_time = hold_time
        self.timer = 0
        self.is_down = False

    def update(self, dt, is_down, is_pressed=False):
        if is_pressed:
            self.is_down = True
        elif not is_down:
            self.is_down = False
        if self.is_down:
            if self.timer >= 0:
                self.timer += dt
                if self.timer >= self.hold_time:
                    self.action()
                    self.timer = -1
        else:
            self.timer = 0


class State:

    def __init__(self):
        self.app = None
        self.draw_state_below = False
        self.buttons = [
            Button("Left"),
            Button("Middle"),
            Button("Right")]
        self.margin_top = Config.margin_top
        self.margin_bottom = Config.margin_top
        self.margin_color = Config.margin_color

    def begin(self):
        self.app.input.bind(
            pygame.K_z, pressed=lambda: self.buttons[0].action())
        self.app.input.bind(
            pygame.K_x, pressed=lambda: self.buttons[1].action())
        self.app.input.bind(
            pygame.K_c, pressed=lambda: self.buttons[2].action())

    def process_input(self):
        pass

    def update(self, dt):
        pass
    
    def on_key_pressed(self, key, mod, text):
        pass
    
    def on_key_released(self, key, mod):
        pass
    
    def on_mouse_pressed(self, pos, button):
        pass

    def on_mouse_released(self, pos, button):
        pass

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()

        # Draw top and bottom margins
        g.fill_rect(0, 0, screen_width, self.margin_top,
                    color=self.margin_color)
        g.fill_rect(0, screen_height - self.margin_bottom,
                    screen_width, self.margin_bottom,
                    color=self.margin_color)
        g.draw_rect(0, 0, screen_width, self.margin_top,
                    thickness=Config.margin_border_thickness,
                    color=Config.margin_border_color)
        g.draw_rect(0, screen_height - self.margin_bottom,
                    screen_width, self.margin_bottom,
                    color=Config.margin_border_color,
                    thickness=Config.margin_border_thickness)

        # Draw buttons
        center_x = screen_width / 2
        center_y = screen_height - (self.margin_bottom / 2)
        for index, button in enumerate(self.buttons):
            text_width, text_height = g.font.size(button.name)
            r = pygame.Rect(center_x, center_y, 0, 0)
            r.inflate_ip(text_width, text_height)
            r.inflate_ip(16, 10)
            r.x += (index - 1) * 200
            g.fill_rect(r.x, r.y, r.width, r.height,
                        color=Config.button_background_color)
            if button.is_down and button.hold_time > 0 and button.timer > 0:
                percent = button.timer / button.hold_time
                g.fill_rect(r.x, r.y, r.width * percent,
                            r.height, color=color.YELLOW)
            g.draw_rect(r.x, r.y, r.width, r.height,
                        thickness=Config.button_border_thickness,
                        color=Config.button_border_color)
            g.draw_text(r.x + (r.width / 2), r.y + (r.height / 2),
                        text=button.name, align=Align.Centered,
                        color=Config.button_text_color)
