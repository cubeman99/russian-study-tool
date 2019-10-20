import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.card_set import CardSet
from study_tool.config import Config
from study_tool.gui.generic_table_widget import GenericTableWidget
from study_tool.gui.card_set_browser_widget import CardSetBrowserWidget
from study_tool.gui.create_card_set_widget import CreateCardSetWidget


class AddCardToSetWidget(widgets.Widget):
    """
    Widget for adding/removing a card from a card set.
    """

    def __init__(self, card: Card, application):
        super().__init__()
        self.set_window_title("Card Sets Containing {}".format(card.get_russian().text))
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
        self.__button_create_set = widgets.Button("Create New Card Set")
        self.__table_card_sets = GenericTableWidget()
        self.__table_card_sets.add_text_column(lambda item: item.get_name(), stretch=1)
        self.__table_card_sets.add_button_column("Remove", self.__on_card_set_clicked, stretch=0)
        self.__table_search_results = GenericTableWidget()
        self.__table_search_results.add_text_column(lambda item: item.get_name())
        self.__table_search_results.add_text_column(lambda item: len(item.get_cards()))
        self.__table_search_results.add_button_column("Add", self.__on_search_card_set_clicked)
        self.__label_result_count = widgets.Label("<result-count>")
        self.__card_set_browser = CardSetBrowserWidget(
            application.card_database.get_root_package(),
            close_on_select=False)

        # Create layouts
        layout_left = widgets.VBoxLayout()
        layout_left.add(self.__label_russian)
        layout_left.add(self.__label_english)
        layout_left.add(self.__label_type)
        layout_left.add(widgets.AbstractScrollArea(self.__table_card_sets))
        layout_left.add(self.__button_apply)
        layout_right = widgets.VBoxLayout()
        layout_search_box = widgets.HBoxLayout()
        layout_search_box.add(widgets.Label("Search:"), stretch=0)
        layout_search_box.add(self.__box_search, stretch=1)
        layout_right.add(layout_search_box)
        layout_right.add(self.__label_result_count)
        layout_right.add(widgets.AbstractScrollArea(self.__table_search_results))
        layout_right.add(self.__card_set_browser)
        layout_right.add(self.__button_create_set)
        layout = widgets.VBoxLayout()
        layout.add(widgets.HBoxLayout(layout_left, layout_right))
        self.set_layout(layout)

        # Connect signals
        self.__box_search.text_edited.connect(self.__on_search_text_changed)
        self.__box_search.return_pressed.connect(self.__on_search_return_pressed)
        self.__button_apply.clicked.connect(self.apply)
        self.__button_create_set.clicked.connect(self.__on_click_create_set)
        self.__card_set_browser.card_set_selected.connect(self.__on_select_card_set)

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
            self.__label_type.set_text(
                "Type: " + self.__card.get_word_type().name)
        else:
            self.__label_type.set_text("Type:")
        self.__label_russian.set_text(
            "Russian: " + repr(self.__card.get_russian()))
        self.__label_english.set_text(
            "English: " + repr(self.__card.get_english()))
        
        self.__table_card_sets.clear()
        for card_set in self.__card_database.iter_card_sets():
            if card_set.has_card(self.__card):
                self.add_card_set(card_set, save=False)
        self.__refresh_search_results()

    def apply(self):
        """Applies changes to the the card."""
        new_card_sets = self.__table_card_sets.get_items()
        changed = False

        # Add/remove the card from card sets
        for card_set in self.__card_database.iter_card_sets():
            if card_set in new_card_sets and not card_set.has_card(self.__card):
                self.__card_database.add_card_to_set(self.__card, card_set)
                changed = True
            elif card_set not in new_card_sets and card_set.has_card(self.__card):
                self.__card_database.remove_card_from_set(self.__card, card_set)
                changed = True

        if changed:
            self.updated.emit(self.__card)
            
    def on_close(self):
        """Called when the widget is closed."""
        self.apply()
        thread = threading.Thread(target=self.__card_database.save_all_changes)
        thread.start()
                    
    def add_card_set(self, card_set: CardSet, save=False):
        """Add a card set to the list of card sets."""
        self.__table_card_sets.add(card_set, enabled=not card_set.is_fixed_card_set())
        self.__refresh_search_results()
        if save:
            self.apply()

    def remove_card_set(self, card_set: CardSet):
        """Remove a card set from the list of card sets."""
        self.__table_card_sets.remove(card_set)
        self.__refresh_search_results()
        self.apply()

    def __on_click_create_set(self):
        """Called when Create New Card Set is clicked."""
        widget = CreateCardSetWidget(
            card_set_package=self.__card_set_browser.get_package(),
            name=self.__box_search.get_text())
        Config.app.push_gui_state(widget)
        widget.card_set_created.connect(self.__on_create_card_set)

    def __on_create_card_set(self, card_set: CardSet):
        """Called when a new Card Set is created."""
        self.__card_set_browser.select_package(card_set.get_package())
        self.add_card_set(card_set)
    
    def __on_search_card_set_clicked(self, card_set: CardSet):
        """Called when a card set in the search results is clicked."""
        self.add_card_set(card_set, save=True)

    def __on_card_set_clicked(self, card_set: CardSet):
        """Called when a card set in the card set list is clicked."""
        self.remove_card_set(card_set)

    def __on_select_card_set(self, card_set: CardSet):
        """Called when a card set in the card set browser is clicked."""
        if self.__table_card_sets.contains(card_set):
            self.remove_card_set(card_set)
        else:
            self.add_card_set(card_set)

    def __on_search_return_pressed(self):
        """Called when pressing enter in the search box."""
        if not self.__table_search_results.get_items():
            return
        card = self.__table_search_results.get_items()[0]
        self.add_card_set(card, save=True)
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
            matching_card_sets = []
            for index, card_set in enumerate(self.__card_database.iter_card_sets()):
                match_score = self.__matches(card_set=card_set, text=text)
                if (match_score is not None and
                        card_set not in self.__table_card_sets.get_items()):
                    matching_card_sets.append((card_set, match_score))

            matching_card_sets.sort(key=lambda x: x[1], reverse=True)
            result_count = len(matching_card_sets)
            for index, (card_set, _) in enumerate(matching_card_sets[:20]):
                enabled = not card_set.is_fixed_card_set()
                row = self.__table_search_results.add(card_set, enabled=enabled)
                #if index == 0:
                #    row.set_color(Color(255, 255, 200))

        self.__label_result_count.set_text("{} results".format(result_count))

    def __matches(self, card_set: CardSet, text: str):
        """Check if a card set matches the given text."""
        text = text.lower().replace("ё", "е")
        name = card_set.get_name().text.lower().replace("ё", "е")
        if text in name:
            return -(len(name) - len(text))
        return None
    