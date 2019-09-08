from cmg.color import Colors
from cmg.color import Color
from cmg.graphics import Align
from cmg.graphics import AccentedText
from study_tool.entities.entity import Entity


class ConjugationTable(Entity):
    """
    Table of word conjugations.
    """

    def __init__(self,
                 font=None,
                 row_count=1,
                 column_count=1,
                 column_widths=None,
                 row_height=22,
                 outline_color=Colors.BLACK,
                 background_color=Colors.WHITE,
                 header_background_color=Color(220),
                 text_color=Colors.BLACK,
                 highlight_color=Colors.YELLOW):
        """Entity constructor."""
        super().__init__()
        self.__row_height = row_height
        self.__table = []
        self.__column_widths = column_widths
        for row in range(row_count):
            self.__table.append([""] * column_count)
        self.__font = font
        self.__text_color = Color(text_color)
        self.__outline_color = Color(outline_color)
        self.__background_color = Color(background_color)
        self.__header_background_color = header_background_color
        self.__highlight_color = Color(highlight_color)
        self.__highlighted_text = None
        self.set_size(sum(self.__column_widths), row_height * row_count)

    def set_highlighted_text(self, text):
        self.__highlighted_text = AccentedText(text)

    def set_text(self, row: int, column: int, text):
        self.__table[row][column] = AccentedText(text)

    def on_create(self):
        """Called when the entity is created."""

    def update(self, dt):
        """Updates the entity."""
         
    def draw(self, g):
        """Draws the entity."""

        # Draw rows
        pos = self.get_position()
        cy = pos.y
        for row_index, row in enumerate(self.__table):
            h = self.__row_height

            # Draw columns
            cx = pos.x
            for column_index, text in enumerate(row):
                w = self.__column_widths[column_index]
                back_color = self.__background_color
                header = row_index == 0 or column_index == 0
                if header:
                    back_color = self.__header_background_color
                elif self.__highlighted_text and text == self.__highlighted_text:
                    back_color = self.__highlight_color

                g.fill_rect(cx, cy, w + 1, h + 1, back_color)
                g.draw_rect(cx, cy, w + 1, h + 1, self.__outline_color, 1)
                g.draw_accented_text(
                    cx + 6, cy + (h / 2),
                    text=AccentedText(text),
                    font=self.__font,
                    color=self.__text_color,
                    align=Align.MiddleLeft)
                cx += w
            cy += h
