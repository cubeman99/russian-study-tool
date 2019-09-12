from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from cmg.application import *
from study_tool.card import Card
from study_tool.config import Config


class CardRow(widgets.Widget):

    def __init__(self, card: Card, select_text="Select", enabled=True):
        super().__init__()
        self.card = card

        self.edit_russian = widgets.TextEdit(repr(card.russian))
        self.edit_english = widgets.TextEdit(repr(card.english))
        self.button_select = widgets.Button(select_text)
        self.button_clicked = self.button_select.clicked

        self.button_select.set_enabled(enabled)
        
        layout = widgets.HBoxLayout()
        layout.add_widget(self.edit_russian, stretch=1)
        layout.add_widget(self.edit_english, stretch=1)
        layout.add_widget(self.button_select, stretch=0)
        self.set_layout(layout)

    def set_color(self, color: Color):
        self.edit_russian.set_background_color(color)
        self.edit_english.set_background_color(color)


class CardListTable(widgets.Widget):
    """
    List of cards, each with a button.
    """
    def __init__(self, select_text: str):
        super().__init__()
        self.__select_text = select_text
        self.__card_to_row_dict = {}
        self.__layout_card_list = widgets.VBoxLayout()
        self.set_layout(self.__layout_card_list)
        self.card_button_clicked = Event(Card)

    def get_row(self, card: Card) -> CardRow:
        return self.__card_to_row_dict.get(card, None)

    def get_cards(self) -> list:
        return list(self.__card_to_row_dict.keys())

    def clear(self):
        self.__layout_card_list.clear()
        self.__card_to_row_dict = {}

    def add(self, card: Card, enabled=True) -> CardRow:
        if card in self.__card_to_row_dict:
            return self.__card_to_row_dict[card]
        row = CardRow(card, select_text=self.__select_text, enabled=enabled)
        row.button_clicked.connect(lambda: self.card_button_clicked.emit(card))
        self.__layout_card_list.add(row)
        self.__card_to_row_dict[card] = row
        return row

    def remove(self, card: Card):
        row = self.__card_to_row_dict[card]
        self.__layout_card_list.remove(row)
        del self.__card_to_row_dict[card]

