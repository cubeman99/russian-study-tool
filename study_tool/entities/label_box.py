import cmg
from cmg.color import Colors
from cmg.color import Color
from cmg.graphics import Align
from cmg.graphics import AccentedText
from cmg.graphics import Graphics
from cmg.math import Vec2
from study_tool.entities.entity import Entity

class LabelBox(Entity):
    """
    A box with a word in it that can reference a card.
    """

    def __init__(self,
                 text: AccentedText,
                 font=None,
                 color=Colors.BLACK,
                 align=Align.Centered,
                 max_font_size=24,
                 min_font_size=12):
        """Entity constructor."""
        super().__init__()
        self.__text = AccentedText(text)
        self.__font = font
        self.__color = Color(color)
        self.__align = align
        self.__min_font_size = min_font_size
        self.__max_font_size = max_font_size

    def get_text(self, text) -> AccentedText:
        return self.__text

    def set_text(self, text):
        self.__text = AccentedText(text)
        self.__recalc_font_size()

    def set_color(self, color: Color):
        self.__color = Color(color)

    def on_create(self):
        """Called when the entity is created."""
        self.__recalc_font_size()

    def update(self, dt):
        """Updates the entity."""
         
    def draw(self, g):
        """Draws the entity."""
        self.__recalc_font_size()
        pos = self.get_center()
        g.draw_accented_text(pos.x,
                             pos.y,
                             text=self.__text,
                             font=self.__font,
                             color=self.__color,
                             align=Align.Centered)

    def __recalc_font_size(self):
        """Recalcs font size."""
        font_size = Graphics(None).get_font_size_to_fit(
            text=self.__text,
            max_font_size=self.__max_font_size,
            min_font_size=self.__min_font_size,
            width=self.get_width())
        self.__font = cmg.Font(font_size)