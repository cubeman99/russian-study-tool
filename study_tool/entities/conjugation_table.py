import cmg
from cmg.color import Color
from study_tool.russian.word import AccentedText
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
                 row_header_count=1,
                 column_header_count=1,
                 outline_color=cmg.Theme.color_outline,
                 background_color=cmg.Theme.color_background,
                 header_background_color=cmg.Theme.color_background_light,
                 text_color=cmg.Theme.color_text,
                 highlight_color=cmg.Theme.color_background_highlighted):
        """Entity constructor."""
        super().__init__()
        self.__row_height = row_height
        self.__column_count = column_count
        self.__row_header_count = row_header_count
        self.__column_header_count = column_header_count
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
        self.__refresh_size()

    def set_row_count(self, row_count: int):
        if row_count < len(self.__table):
            self.__table = self.__table[:row_count]
        while len(self.__table) < row_count:
            self.__table.append([""] * self.__column_count)
        self.__refresh_size()

    def add_row(self, column_text: list):
        self.__table.append(list(column_text))
        self.__refresh_size()

    def __refresh_size(self):
        self.set_size(sum(self.__column_widths),
                      self.__row_height * len(self.__table))

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
                header = (row_index < self.__row_header_count or
                          column_index < self.__column_header_count)
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
                    align=cmg.Align.MiddleLeft)
                cx += w
            cy += h
