import pygame
import cmg
from cmg.color import Colors
from cmg.color import Color
from cmg import math
from study_tool import card_attributes
from study_tool.card import Card
from study_tool.card_attributes import *
from study_tool.entities.entity import Entity
from study_tool.russian.word import AccentedText
from study_tool.russian.word import Word


class CardAttributeBox(Entity):
    """
    A box with a word in it that can reference a card.
    """

    def __init__(self, attribute, short=False, font=None):
        """Entity constructor."""
        super().__init__()
        self.__attribute = CardAttributes(attribute)
        self.__short = short
        self.__text = ""
        self.__font = font
        if self.__font is None:
            self.__font = cmg.Font(24)
        self.__padding = cmg.Vec2(8, 6)

    def on_create(self):
        """Called when the entity is created."""
        if self.__short:
            self.__text = self.__attribute.value
        else:
            self.__text = card_attributes.get_card_attribute_display_name(
                self.__attribute)
        self.set_size(self.__font.measure(self.__text) + (self.__padding * 2))

    def update(self, dt):
        """Updates the entity."""
            
    def draw(self, g):
        """Draws the entity."""
        # Determine colors
        text_color = Colors.WHITE
        background_color = Colors.BLACK
        if self.__attribute in card_attributes.ATTRIBUTE_COLORS:
            background_color = card_attributes.ATTRIBUTE_COLORS[self.__attribute]
            
        # Draw the background
        g.fill_rect(self.get_rect(),
                    color=background_color)

        # Draw the text
        g.draw_accented_text(self.get_center().x,
                             self.get_center().y,
                             text=self.__text,
                             font=self.__font,
                             color=text_color,
                             align=cmg.Align.Centered)
