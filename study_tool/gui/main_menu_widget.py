import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetPackage
from study_tool.config import Config
from study_tool.gui.generic_table_widget import GenericTableWidget
from study_tool.scheduler import SchedulerParams
from study_tool.states.read_text_state import ReadTextState
from study_tool.states.study_state import StudyParams
from study_tool.states.sub_menu_state import SubMenuState
from study_tool.entities.study_proficiency_bar import StudyProficiencyBar
from study_tool.gui.query_widget import QueryWidget
from study_tool.gui.create_card_set_widget import CreateCardSetWidget
from study_tool.query import CardQuery


class MainMenuWidget(widgets.Widget):
    """
    Widget for browsing card sets and packages in the main menu.
    """
    def __init__(self, card_set_package: CardSetPackage):
        super().__init__()
        self.__package = card_set_package

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

    def is_root_package(self) -> bool:
        return not self.__package.get_parent()

    def get_package(self) -> CardSetPackage:
        """Gets the current package being browsed."""
        return self.__package
                
    def select_package(self, package: CardSetPackage):
        """Start browsing a new card set package."""
        if package is None:
            self.close()
            return

        self.__package = package
        
        # Set title
        if self.is_root_package():
            self.set_window_title("Russian Study Tool")
        else:
            self.set_window_title(self.__package.get_name())

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

        # Create the back button
        back_button = None
        if self.is_root_package():
            back_button = widgets.Button("Quit")
            back_button.clicked.connect(self.close)
        else:
            back_button = widgets.Button("[Back]")
            back_button.clicked.connect(lambda: self.select_package(package.get_parent()))
        self.__list_layout.add(back_button)

        # Create buttons for each sub-package
        for sub_package in package.get_packages():
            button = self.__create_package_button(sub_package)
            self.__list_layout.add(button)

        # Create buttons for each card set
        for card_set in package.get_card_sets():
            button = self.__create_card_set_button(card_set)
            self.__list_layout.add(button)
                
        # Create buttons for package itself
        select_button = widgets.Button(self.__package.get_name().text)
        #select_button.clicked.connect(lambda: self.__on_select_package(package))
        self.__list_layout.add(select_button)
        
        if back_button:
            back_button.focus()

    def __create_path_button(self, package: CardSetPackage) -> widgets.Button:
        button = widgets.Button(package.get_name().text)
        button.clicked.connect(lambda: self.select_package(package))
        return button

    def __create_package_button(self, package: CardSetPackage) -> widgets.Button:
        name = "[...] {}".format(package.get_name().text)
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

    def __on_select_package(self, package: CardSetPackage):
        """Selects a card set package."""

    def __on_select_card_set(self, card_set: CardSet):
        """Selects a card set."""
        
        sub_menu = SubMenuState(card_set.get_name())
        options = []
        sub_menu.add_option(
            "Quiz Random Sides",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                study_params=StudyParams(random_side=True)))
        sub_menu.add_option(
            "Quiz Random Forms",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                study_params=StudyParams(random_side=True,
                                         random_form=True)))
        sub_menu.add_option(
            "Quiz English",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                study_params=StudyParams(shown_side=CardSide.English)))
        sub_menu.add_option(
            "Quiz Russian",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                study_params=StudyParams(shown_side=CardSide.Russian)))
        sub_menu.add_option(
            "Quiz New Cards",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                card_query=CardQuery(max_proficiency=0),
                study_params=StudyParams(random_side=True),
                scheduler_params=SchedulerParams(max_repetitions=1)))
        sub_menu.add_option(
            "Quiz Problem Cards",
            lambda: Config.app.push_study_state(
                card_set=card_set,
                card_query=CardQuery(max_score=0.9),
                study_params=StudyParams(random_side=True)))
        sub_menu.add_option(
            "Query",
            lambda: Config.app.push_gui_state(
                QueryWidget(Config.app, card_set)))
        sub_menu.add_option(
            "List",
            lambda: Config.app.push_card_list_state(card_set))

        if isinstance(card_set, CardSet) and not card_set.is_fixed_card_set():
            sub_menu.add_option(
                "Edit", lambda: Config.app.push_card_set_edit_state(card_set))

        if card_set is self.__package:
            sub_menu.add_option(
                "Create New Set",
                lambda: Config.app.push_gui_state(
                    CreateCardSetWidget(self.__package)))

        if isinstance(card_set, CardSet) and card_set.is_fixed_card_set():
            old_file_path = card_set.get_file_path()
            card_sets_in_file = Config.app.card_database.get_card_sets_from_path(old_file_path)
            if len(card_sets_in_file) > 1:
                text = "Assimilate {} sets to YAML".format(len(card_sets_in_file))
            else:
                text = "Assimilate to YAML"
            sub_menu.add_option(
                text, lambda: Config.app.assimilate_card_set_to_yaml(card_set))

        sub_menu.add_option("Cancel", None)
        Config.app.push_state(sub_menu)