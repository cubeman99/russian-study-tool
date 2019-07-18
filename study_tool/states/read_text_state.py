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
from study_tool.card import *
from study_tool.card_set import *
from study_tool.menu import Menu
from study_tool.states.state import *
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.example_database import split_words


class ReadTextState(State):
    def __init__(self):
        super().__init__()
        self.text_font = pygame.font.Font(None, 28)

    def begin(self):
        self.buttons[0] = Button("Scroll Up")
        self.buttons[1] = Button("Menu", self.pause)
        self.buttons[2] = Button("Scroll Down")
        self.cursor = 0
        self.text = AccentedText("У тебя вступление просто огромное, я тоже люблю такие форматы, но блин вступление на пол-ролика бесит, говоришь одно и то же Мне лично Maud не понравилась, совершенно банальный персонаж, которого даже не попытались развить, который к тому же еще и перечит серии Cutie Mark Chronicles... Кстати девушки-брони вроде бы Pegasisters))﻿")
        self.text = AccentedText("")
        for para in self.app.example_database.stories[2].chapters[0].paragraphs:
            self.text += para
        self.words = list(split_words(self.text.text))
        self.paragraphs = [(AccentedText(p), list(split_words(AccentedText(p).text)))
                           for p in self.app.example_database.stories[2].chapters[0].paragraphs]

    def pause(self):
        self.app.push_state(SubMenuState(
            "Pause",
            [("Resume", None),
             ("Menu", self.app.pop_state),
                ("Exit", self.app.quit)]))

    def update(self, dt):
        move = self.app.inputs[2].get_amount(
        ) - self.app.inputs[0].get_amount()
        speed = 1000.0
        self.cursor += move * dt * speed

    def draw(self, g):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        bottom = screen_height - self.margin_bottom

        cursor_x = 40
        cursor_y = self.margin_top + 40
        cursor_y -= self.cursor
        for paragraph_text, paragraph_words in self.paragraphs:
            last_index = 0
            if cursor_y > bottom:
                break
            for name, start_index in paragraph_words:
                if cursor_y > bottom:
                    break
                start_index -= 1
                end_index = start_index + len(name)
                text = paragraph_text.text[last_index:end_index]
                pretext = paragraph_text.text[last_index:start_index]
                last_index = end_index
                cards = list(self.app.card_database.find_cards_by_word(name))

                w, h = g.measure_text(text, font=self.text_font)
                if cursor_x + w > screen_width - 80:
                    cursor_x = 40
                    cursor_y += 24
                visible = cursor_y > self.margin_top - 30
                if len(pretext) > 0:
                    if visible:
                        g.draw_text(cursor_x, cursor_y, text=pretext,
                                    font=self.text_font,
                                    color=color.BLACK)
                    cursor_x += g.measure_text(pretext, font=self.text_font)[0]
                word_color = color.BLACK
                w, h = g.measure_text(name, font=self.text_font)
                if visible:
                    if len(cards) > 0:
                        back_color = math.lerp(
                            color.RED, color.GREEN, t=cards[0].get_history_score())
                        g.fill_rect(cursor_x, cursor_y, w, h, color=back_color)
                    else:
                        back_color = color.GRAY
                        words = list(self.app.word_database.lookup_word(name))
                        if len(words) > 0:
                            back_color = color.BLUE
                        g.draw_rect(cursor_x, cursor_y, w, h, color=back_color)
                    if cards:
                        word_color = color.BLACK
                    g.draw_text(cursor_x, cursor_y, text=name,
                                font=self.text_font,
                                color=word_color)
                cursor_x += g.measure_text(name, font=self.text_font)[0]

            cursor_x = 40
            cursor_y += 24 * 2

        # Draw state
        State.draw(self, g)
