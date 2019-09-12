from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.config import Config
from study_tool.gui.card_list_table import CardListTable


class RelatedCardsWidget(widgets.Widget):
    """
    Widget for editing a card's related cards.
    """

    def __init__(self, card: Card, application):
        super().__init__()
        self.__card = card
        self.__application = application
        self.__card_database = application.card_database
        self.__search_result_cards = []
        self.updated = Event(Card)

        # Create widgets
        self.__box_search = widgets.TextEdit()
        self.__label_russian = widgets.Label("<russian>")
        self.__label_english = widgets.Label("<english>")
        self.__label_type = widgets.Label("<type>")
        self.__button_apply = widgets.Button("Apply")
        self.__button_cancel = widgets.Button("Cancel")
        self.__table_related_cards = CardListTable(select_text="Remove")
        self.__table_searched_cards = CardListTable(select_text="Add")
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
        self.__button_apply.clicked.connect(self.save)
        self.__button_cancel.clicked.connect(self.__on_click_cancel)
        self.__table_searched_cards.card_button_clicked.connect(self.__on_search_card_clicked)
        self.__table_related_cards.card_button_clicked.connect(self.__on_related_card_clicked)

        self.select_card(card)
        self.__box_search.focus()
                
    def get_card(self) -> Card:
        """Get the card being edited."""
        return self.__card

    def select_card(self, card: Card):
        """Sets the card that is being edited."""
        # Initialize with card data
        self.__card = card
        if self.__card.get_word_type() is not None:
            self.__label_type.set_text(self.__card.get_word_type().name)
        else:
            self.__label_type.set_text("")
        self.__label_russian.set_text(repr(self.__card.get_russian()))
        self.__label_english.set_text(repr(self.__card.get_english()))
        
        self.__table_related_cards.clear()
        for card in self.__card.get_related_cards():
            self.add_related_card(card, save=False)
        self.__refresh_search_results()

    def save(self):
        """Save the card changes."""
        new_cards = self.__table_related_cards.get_cards()
        old_cards = list(self.__card.get_related_cards())
        touched_cards = set()

        # Add new related cards
        for new_card in new_cards:
            if new_card not in old_cards:
                Config.logger.info("Linking related cards '{}' and '{}'"
                                    .format(repr(self.__card.get_russian()),
                                            repr(new_card.get_russian())))
                self.__card.add_related_card(new_card)
                new_card.add_related_card(self.__card)
                touched_cards.add(self.__card)
                touched_cards.add(new_card)

        # Remove old related cards
        for old_card in old_cards:
            if old_card not in new_cards:
                Config.logger.info("Unlinking related cards '{}' and '{}'"
                                    .format(repr(self.__card.get_russian()),
                                            repr(old_card.get_russian())))
                self.__card.remove_related_card(old_card)
                old_card.remove_related_card(self.__card)
                touched_cards.add(self.__card)
                touched_cards.add(old_card)

        # Save all card data
        if touched_cards:
            self.__application.save_card_data()
            self.updated.emit(self.__card)

    def __on_click_cancel(self):
        """Cancel the card changes."""
        self.close()
            
    def add_related_card(self, card: Card, save=False):
        """Add a related card to the list of related cards."""
        self.__table_related_cards.add(card)
        self.__refresh_search_results()
        if save:
            self.save()

    def remove_related_card(self, card: Card):
        """Remove a related card from the list of related cards."""
        self.__table_related_cards.remove(card)
        self.__refresh_search_results()
    
    def __on_search_card_clicked(self, card: Card):
        """Called when a card in the search results is clicked."""
        self.add_related_card(card, save=True)

    def __on_related_card_clicked(self, card: Card):
        """Called when a card in the related cards is clicked."""
        self.remove_related_card(card)

    def __on_search_return_pressed(self):
        """Called when pressing enter in the search box."""
        if not self.__search_result_cards:
            return
        card = self.__search_result_cards[0]
        self.add_related_card(card, save=True)
        self.__box_search.select_all()

    def __on_search_text_changed(self):
        """Called when the search box text changes."""
        self.__refresh_search_results()

    def __refresh_search_results(self):
        """Refresh the list of card search results."""
        text = self.__box_search.get_text()
        self.__table_searched_cards.clear()
        self.__search_result_cards = []
        result_count = 0
        
        if text.strip():
            matching_cards = []
            for index, card in enumerate(self.__card_database.iter_cards()):
                match_score = self.__matches(card, text)
                if (match_score is not None and
                        card not in self.__table_related_cards.get_cards() and
                        card is not self.__card):
                    matching_cards.append((card, match_score))

            matching_cards.sort(key=lambda x: x[1], reverse=True)
            result_count = len(matching_cards)
            for index, (card, _) in enumerate(matching_cards[:20]):
                enabled = not card.is_in_fixed_card_set()
                row = self.__table_searched_cards.add(card, enabled=enabled)
                self.__search_result_cards.append(card)
                if index == 0:
                    row.set_color(Color(255, 255, 200))

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
    