from cmg.color import Colors
from cmg.color import Color
from cmg.graphics import Align
from cmg.graphics import AccentedText
from cmg.graphics import Graphics
from cmg.math import Vec2
from study_tool.entities.entity import Entity

class TextLabel(Entity):
    """
    A box with a word in it that can reference a card.
    """

    def __init__(self,
                 text: AccentedText,
                 font=None,
                 color=Colors.BLACK,
                 align=Align.TopLeft):
        """Entity constructor."""
        super().__init__()
        self.__text = AccentedText(text)
        self.__color = Color(color)
        self.__font = font
        self.__align = align

    def get_text(self, text) -> AccentedText:
        return self.__text

    def set_text(self, text):
        self.__text = AccentedText(text)
        self.set_size(Graphics(None).measure_text(self.__text, font=self.__font))

    def set_color(self, color: Color):
        self.__color = Color(color)

    def on_create(self):
        """Called when the entity is created."""
        self.set_size(Graphics(None).measure_text(self.__text, font=self.__font))

    def update(self, dt):
        """Updates the entity."""
         
    def draw(self, g):
        """Draws the entity."""
        pos = self.get_position()
        g.draw_accented_text(pos.x,
                             pos.y,
                             text=self.__text,
                             font=self.__font,
                             color=self.__color,
                             align=self.__align)