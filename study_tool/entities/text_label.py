import cmg
from cmg.color import Color
from study_tool.russian.word import AccentedText
from study_tool.entities.entity import Entity

class TextLabel(Entity):
    """
    A box with a word in it that can reference a card.
    """

    def __init__(self,
                 text: AccentedText,
                 font=None,
                 color=None,
                 align=cmg.Align.TopLeft):
        """Entity constructor."""
        super().__init__()
        self.__text = AccentedText(text)
        self.__color = Color(color) if color else cmg.Theme.color_text
        self.__font = font
        self.__align = align

    def get_text(self, text) -> AccentedText:
        return self.__text

    def set_text(self, text):
        self.__text = AccentedText(text)
        self.set_size(cmg.Graphics(None).measure_text(self.__text, font=self.__font))

    def set_color(self, color: Color):
        self.__color = Color(color)

    def on_create(self):
        """Called when the entity is created."""
        self.set_size(cmg.Graphics(None).measure_text(self.__text, font=self.__font))

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
