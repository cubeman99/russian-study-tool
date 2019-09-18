import pygame
import cmg
from cmg.color import Colors
from cmg.color import Color
from cmg.graphics import Align
from cmg.graphics import Graphics
from cmg.graphics import AccentedText
from cmg.math import Vec2
from cmg import math
from study_tool.entities.entity import Entity
from study_tool.card import Card
from study_tool.russian.word import Word


class WordBox(Entity):
    """
    A box with a word in it that can reference a card.
    """

    def __init__(self, word, font=None):
        """Entity constructor."""
        super().__init__()
        if isinstance(word, Card):
            self.__text = AccentedText(word.get_russian())
            self.__word = word.get_word()
            self.__cards = [word]
        elif isinstance(word, Word):
            self.__text = AccentedText(word.name)
            self.__word = word
            self.__cards = None
        else:
            self.__text = AccentedText(word)
            self.__word = None
            self.__cards = None
        self.__font = font
        if self.__font is None:
            self.__font = cmg.Font(24)
        self.__padding = Vec2(4, 2)
        self.__size = Vec2(0, 0)

    def on_create(self):
        """Called when the entity is created."""
        if not self.__word:
            self.__word = self.context.word_database.lookup_word(self.__text.text)
        if not self.__cards:
            self.__cards = list(self.context.card_database.find_cards_by_word(self.__text.text))
        self.__size = Graphics(None).measure_text(self.__text, font=self.__font)
        self.set_size(self.__size + (self.__padding * 2))

    def update(self, dt):
        """Updates the entity."""
            
    def draw(self, g):
        """Draws the entity."""
        pos = self.get_position()
        size = self.__size

        # Determine colors
        background_color = Colors.WHITE
        outline_color = Colors.LIGHT_GRAY
        text_color = Colors.BLACK
        if self.__word:
            outline_color = Colors.BLUE
        if self.__cards:
            outline_color = Colors.BLACK
            card = self.__cards[0]
            study_data = self.context.study_database.get_card_study_data(card)
            background_color = math.lerp(
                Color(255, 128, 128),
                Color(128, 255, 128),
                t=study_data.get_history_score())
            
        # Draw the background
        g.fill_rect(pos.x,
                    pos.y,
                    self.__size.x + (self.__padding.x * 2),
                    self.__size.y + (self.__padding.y * 2),
                    color=background_color)

        # Draw the outline
        g.draw_rect(pos.x,
                    pos.y,
                    self.__size.x + (self.__padding.x * 2),
                    self.__size.y + (self.__padding.y * 2),
                    color=outline_color)
        
        # Draw the text
        g.draw_accented_text(pos.x + self.__padding.x,
                             pos.y + self.__padding.y,
                             text=self.__text,
                             font=self.__font,
                             color=text_color,
                             align=Align.TopLeft)