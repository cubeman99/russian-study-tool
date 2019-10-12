import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.russian.word import AccentedText
from study_tool.card import Card
from study_tool.card_set import CardSet
from study_tool.config import Config
from study_tool.gui.generic_table_widget import GenericTableWidget
from study_tool.gui.card_set_browser_widget import CardSetBrowserWidget
from study_tool.gui.create_card_set_widget import CreateCardSetWidget


class CardSearchWidget(widgets.Widget):
    """
    Widget to search for cards.
    """

    def __init__(self, enabled_func=None, visible_func=None):
        super().__init__()
        self.card_clicked = Event(Card)
        self.__enabled_func = enabled_func
        self.__visible_func = visible_func

        # Create widgets
        self.__box_search = widgets.TextEdit()
        self.__label_result_count = widgets.Label("<result-count>")
        self.__table_search_results = GenericTableWidget()
        self.__table_search_results.add_text_column(lambda card: card.get_russian().text)
        self.__table_search_results.add_text_column(lambda card: card.get_english().text)
        self.__table_search_results.add_button_column("Add", self.__on_search_card_clicked)

        # Create layouts
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(widgets.Label("Search:"), self.__box_search))
        layout.add(widgets.HBoxLayout(widgets.Label("Results:"), self.__label_result_count))
        layout.add(self.__table_search_results)
        self.set_layout(layout)

        # Connect signals
        self.__box_search.text_edited.connect(self.__on_search_text_changed)
        self.__box_search.return_pressed.connect(self.__on_search_return_pressed)
        
    def get_first_result(self) -> Card:
        if self.__table_search_results.get_items():
            return self.__table_search_results.get_items()[0]
        return None

    def get_results(self) -> list:
        return self.__table_search_results.get_items()
    
    def get_search_text(self) -> str:
        return self.__box_search.get_text()

    def add_button_column(self, name: str, callback):
        self.__table_search_results.add_button_column(name, callback)

    def remove_first_result(self) -> Card:
        if self.__table_search_results.get_items():
            first_item = self.__table_search_results.get_items()[0]
            self.__table_search_results.remove(first_item)
            return first_item
        return None

    def remove_from_results(self, card: Card):
        self.__table_search_results.remove(card)

    def refresh(self):
        self.__refresh_search_results()

    def set_search_text(self, text):
        text = AccentedText(text).text
        self.__box_search.set_text(text)
        self.__on_search_text_changed()

    def __on_search_card_clicked(self, card: Card):
        """Called when a card in the search results is clicked."""
        self.card_clicked.emit(card)

    def __on_search_return_pressed(self):
        """Called when pressing enter in the search box."""
        results = self.__table_search_results.get_items()
        if not results:
            return
        card = results[0]
        if card.is_in_fixed_card_set():
            return
        self.card_clicked.emit(card)
        self.__box_search.select_all()

    def __on_search_text_changed(self):
        """Called when the search box text changes."""
        self.__refresh_search_results()

    def __refresh_search_results(self):
        """Refresh the list of card search results."""
        text = self.__box_search.get_text()
        self.__table_search_results.clear()
        result_count = 0
        
        if text.strip():
            matching_cards = []
            for index, card in enumerate(Config.app.card_database.iter_cards()):
                match_score = self.__matches(card, text)
                if match_score is not None:
                    matching_cards.append((card, match_score))

            matching_cards.sort(key=lambda x: x[1], reverse=True)
            result_count = len(matching_cards)
            for index, (card, _) in enumerate(matching_cards[:20]):
                enabled = not card.is_in_fixed_card_set()
                if self.__enabled_func and enabled and not self.__enabled_func(card):
                    enabled = False
                color = None
                if index == 0:
                    color = Color(255, 255, 200)
                row = self.__table_search_results.add(
                    card, enabled=enabled, color=color)

        self.__label_result_count.set_text("{} results".format(result_count))

    def __matches(self, card: Card, text: str):
        """Check if a card matches the given text."""
        if self.__visible_func and not self.__visible_func(card):
            return None
        text = text.lower().replace("ё", "е")
        russian = card.get_russian().text.lower().replace("ё", "е")
        english = card.get_english().text.lower()
        if text in russian:
            return -(len(russian) - len(text))
        if text in english:
            return -(len(english) - len(text))
        return None
    