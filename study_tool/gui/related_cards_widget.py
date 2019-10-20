import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.config import Config
from study_tool.gui.generic_table_widget import GenericTableWidget


class RelatedCardsWidget(widgets.Widget):
    """
    Widget for editing a card's related cards.
    """

    def __init__(self, card: Card, application):
        super().__init__()
        self.set_window_title("Edit Related Cards for {}".format(card.get_russian().text))
        self.__card = card
        self.__application = application
        self.__card_database = application.card_database
        self.updated = Event(Card)

        # Create widgets
        self.__box_search = widgets.TextEdit()
        self.__label_russian = widgets.Label("<russian>")
        self.__label_english = widgets.Label("<english>")
        self.__label_type = widgets.Label("<type>")
        self.__button_apply = widgets.Button("Apply")
        self.__button_cancel = widgets.Button("Cancel")
        self.__table_related_cards = GenericTableWidget()
        self.__table_related_cards.add_text_column(lambda card: card.get_russian().text)
        self.__table_related_cards.add_text_column(lambda card: card.get_english().text)
        self.__table_related_cards.add_button_column("Remove", self.__on_related_card_clicked)
        self.__table_searched_cards = GenericTableWidget()
        self.__table_searched_cards.add_text_column(lambda card: card.get_russian().text)
        self.__table_searched_cards.add_text_column(lambda card: card.get_english().text)
        self.__table_searched_cards.add_button_column("Add", self.__on_search_card_clicked)
        self.__label_result_count = widgets.Label("<result-count>")

        # Create layouts
        layout_left = widgets.VBoxLayout()
        layout_left.add(self.__label_russian)
        layout_left.add(self.__label_english)
        layout_left.add(self.__label_type)
        layout_left.add(widgets.AbstractScrollArea(self.__table_related_cards))
        layout_right = widgets.VBoxLayout()
        layout_search_box = widgets.HBoxLayout()
        layout_search_box.add(widgets.Label("Search:"), stretch=0)
        layout_search_box.add(self.__box_search, stretch=1)
        layout_right.add(layout_search_box)
        layout_right.add(self.__label_result_count)
        layout_right.add(widgets.AbstractScrollArea(self.__table_searched_cards))
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(layout_left, layout_right))
        layout.add(widgets.HBoxLayout(self.__button_apply, self.__button_cancel))
        self.set_layout(layout)

        # Connect signals
        self.__box_search.text_edited.connect(self.__on_search_text_changed)
        self.__box_search.return_pressed.connect(self.__on_search_return_pressed)
        self.__button_apply.clicked.connect(self.apply)
        self.__button_cancel.clicked.connect(self.__on_click_cancel)

        self.select_card(card)
        self.__box_search.focus()
                
    def get_card(self) -> Card:
        """Get the card being edited."""
        return self.__card

    def select_card(self, card: Card):
        """Sets the card that is being edited."""
        self.__card = card

        if self.__card.get_word_type() is not None:
            self.__label_type.set_text(
                "Type: " + self.__card.get_word_type().name)
        else:
            self.__label_type.set_text("Type:")
        self.__label_russian.set_text(
            "Russian: " + repr(self.__card.get_russian()))
        self.__label_english.set_text(
            "English: " + repr(self.__card.get_english()))
        
        self.__table_related_cards.clear()
        for card in self.__card.get_related_cards():
            self.add_related_card(card, save=False)
        self.__refresh_search_results()

    def apply(self):
        """Applies changes to the the card."""
        new_related_cards = self.__table_related_cards.get_items()
        updated_card = Card(copy=self.__card,
                            related_cards=new_related_cards)
        changed = self.__card_database.update_card(
            original=self.__card, modified=updated_card)
        if changed:
            self.updated.emit(self.__card)
            
    def on_close(self):
        """Called when the widget is closed."""
        thread = threading.Thread(target=self.__card_database.save_all_changes)
        thread.start()

    def __on_click_cancel(self):
        """Cancel the card changes."""
        self.close()
            
    def add_related_card(self, card: Card, save=False):
        """Add a related card to the list of related cards."""
        self.__table_related_cards.add(card)
        self.__refresh_search_results()
        if save:
            self.apply()

    def remove_related_card(self, card: Card):
        """Remove a related card from the list of related cards."""
        self.__table_related_cards.remove(card)
        self.__refresh_search_results()
        self.apply()
    
    def __on_search_card_clicked(self, card: Card):
        """Called when a card in the search results is clicked."""
        self.add_related_card(card, save=True)

    def __on_related_card_clicked(self, card: Card):
        """Called when a card in the related cards is clicked."""
        self.remove_related_card(card)

    def __on_search_return_pressed(self):
        """Called when pressing enter in the search box."""
        results = self.__table_searched_cards.get_items()
        if not results:
            return
        card = results[0]
        if card.is_in_fixed_card_set():
            return
        self.add_related_card(card, save=True)
        self.__box_search.select_all()

    def __on_search_text_changed(self):
        """Called when the search box text changes."""
        self.__refresh_search_results()

    def __refresh_search_results(self):
        """Refresh the list of card search results."""
        text = self.__box_search.get_text()
        self.__table_searched_cards.clear()
        result_count = 0
        
        if text.strip():
            matching_cards = []
            for index, card in enumerate(self.__card_database.iter_cards()):
                match_score = self.__matches(card, text)
                if (match_score is not None and
                        card not in self.__table_related_cards.get_items() and
                        card is not self.__card):
                    matching_cards.append((card, match_score))

            matching_cards.sort(key=lambda x: x[1], reverse=True)
            result_count = len(matching_cards)
            for index, (card, _) in enumerate(matching_cards[:20]):
                enabled = not card.is_in_fixed_card_set()
                color = None
                if index == 0:
                    color = Color(255, 255, 200)
                row = self.__table_searched_cards.add(
                    card, enabled=enabled, color=color)

        self.__label_result_count.set_text("{} results".format(result_count))

    def __matches(self, card: Card, text: str):
        """Check if a card matches the given text."""
        text = text.lower().replace("ё", "е")
        russian = card.get_russian().text.lower().replace("ё", "е")
        english = card.get_english().text.lower()
        if text in russian:
            return -(len(russian) - len(text))
        if text in english:
            return -(len(english) - len(text))
        return None
    