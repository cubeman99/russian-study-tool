import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetPackage
from study_tool.config import Config
from study_tool.gui.generic_table_widget import GenericTableWidget


class CardSetBrowserWidget(widgets.Widget):
    """
    Widget for browsing card sets like a file explorer.
    """
    def __init__(self, card_set_package: CardSetPackage,
                 card_set_mode=True, close_on_select=True):
        super().__init__()
        self.__package = card_set_package
        self.__card_set_mode = card_set_mode
        self.__close_on_select = close_on_select

        if self.__card_set_mode:
            self.set_window_title("Browse Card Sets")
        else:
            self.set_window_title("Browse Packages")

        # Events
        self.canceled = Event()
        self.card_set_selected = Event(CardSet)
        self.package_selected = Event(CardSetPackage)
        self.package_changed = Event(CardSetPackage)

        # Create widgets
        self.__grid_layout = widgets.GridLayout()

        # Create layouts
        self.__path_bar_layout = widgets.HBoxLayout()
        self.__list_widget = widgets.Widget()
        self.__list_layout = widgets.VBoxLayout()
        self.__list_widget.set_layout(self.__list_layout)
        top_layout = widgets.HBoxLayout()
        top_layout.add(widgets.Label("Path:"), stretch=0)
        top_layout.add(self.__path_bar_layout, stretch=0)
        top_layout.add(widgets.Label(""), stretch=1)
        layout = widgets.VBoxLayout()
        layout.add(top_layout)
        layout.add(widgets.AbstractScrollArea(self.__list_widget))
        self.set_layout(layout)

        self.select_package(card_set_package)

    def get_package(self) -> CardSetPackage:
        """Gets the current package being browsed."""
        return self.__package
                
    def select_package(self, package: CardSetPackage):
        """Start browsing a new card set package."""
        if package is None:
            self.canceled.emit()
            self.close()
            return

        self.__package = package

        # Create the path list buttons
        path_buttons = []
        parent = package
        while parent:
            button = self.__create_path_button(parent)
            path_buttons.insert(0, button)
            parent = parent.get_parent()
        self.__path_bar_layout.clear()
        for button in path_buttons:
            self.__path_bar_layout.add(button)

        self.__list_layout.clear()

        back_button = None
        if self.__close_on_select or package.get_parent():
            back_button = widgets.Button("[Back]")
            back_button.clicked.connect(lambda: self.select_package(package.get_parent()))
            self.__list_layout.add(back_button)

        for sub_package in package.get_packages():
            button = self.__create_package_button(sub_package)
            self.__list_layout.add(button)

        if not self.__card_set_mode:
            select_button = widgets.Button("[Select]")
            select_button.clicked.connect(lambda: self.__on_select_package(package))
            self.__list_layout.add(select_button)

        if self.__card_set_mode:
            for card_set in package.get_card_sets():
                button = self.__create_card_set_button(card_set)
                self.__list_layout.add(button)
        
        if back_button:
            back_button.focus()
        self.package_changed.emit(package)

    def __create_path_button(self, package: CardSetPackage) -> widgets.Button:
        button = widgets.Button(package.get_name().text)
        button.clicked.connect(lambda: self.select_package(package))
        return button

    def __create_package_button(self, package: CardSetPackage) -> widgets.Button:
        if self.__card_set_mode:
            name = "[...] {}".format(package.get_name().text)
        else:
            name = package.get_name().text
        button = widgets.Button(name)
        button.clicked.connect(lambda: self.select_package(package))
        return button

    def __create_card_set_button(self, card_set: CardSet) -> widgets.Button:
        name = card_set.get_name().text
        if card_set.is_fixed_card_set():
            name += " [txt]"
        button = widgets.Button(name)
        button.clicked.connect(lambda: self.__on_select_card_set(card_set))
        return button

    def __on_select_card_set(self, card_set: CardSet):
        """Selects a card set."""
        self.card_set_selected.emit(card_set)
        if self.__close_on_select:
            self.close()

    def __on_select_package(self, package: CardSetPackage):
        """Selects a card set package."""
        self.package_selected.emit(package)
        if self.__close_on_select:
            self.close()


class CardSetPackageBrowserWidget(CardSetBrowserWidget):
    """
    Widget for browsing card set packages like a file explorer.
    """
    def __init__(self, card_set_package: CardSetPackage, close_on_select=True):
        super().__init__(card_set_package=card_set_package,
                         card_set_mode=False,
                         close_on_select=close_on_select)
