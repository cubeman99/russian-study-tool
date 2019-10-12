import threading
from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.card import Card
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetPackage
from study_tool.config import Config
from study_tool.gui.card_set_browser_widget import CardSetPackageBrowserWidget


class CreateCardSetWidget(widgets.Widget):
    """
    Widget for creating a new card set (but not for adding cards to it).
    """
    def __init__(self, card_set_package: CardSetPackage, name=""):
        super().__init__()
        self.__package = card_set_package

        self.set_window_title("Create New Card Set")

        # Events
        self.canceled = Event()
        self.card_set_created = Event(CardSet)

        # Create widgets
        self.__grid_layout = widgets.GridLayout()
        self.__edit_display_name = widgets.TextEdit(name)
        self.__edit_file_name = widgets.TextEdit("")
        self.__edit_path = widgets.TextEdit(self.get_path())
        self.__checkbox_auto_file_name = widgets.CheckBox("Auto", checked=True)
        self.__button_browse = widgets.Button("Browse")
        self.__button_create = widgets.Button("Create")
        self.__button_cancel = widgets.Button("Cancel")

        # Create layouts
        layout = widgets.VBoxLayout()
        layout.add(self.__edit_display_name)
        layout.add(widgets.HBoxLayout(widgets.Label("Display Name:"),
                                      self.__edit_display_name))
        layout.add(widgets.HBoxLayout(widgets.Label("File Name:"),
                                      self.__edit_file_name,
                                      self.__checkbox_auto_file_name))
        layout.add(widgets.HBoxLayout(widgets.Label("Path:"),
                                      self.__edit_path,
                                      self.__button_browse))
        layout.add(widgets.HBoxLayout(self.__button_create,
                                      self.__button_cancel))
        self.set_layout(layout)

        # Connect signals
        self.__button_browse.clicked.connect(self.__on_click_browse)
        self.__button_create.clicked.connect(self.__on_click_create)
        self.__button_cancel.clicked.connect(self.__on_click_cancel)
        self.__checkbox_auto_file_name.clicked.connect(self.__on_click_auto)
        self.__edit_display_name.text_edited.connect(self.__on_display_name_edited)

        self.__on_click_auto()
        self.__edit_display_name.focus()

    def get_path(self) -> str:
        """Gets the current package being browsed."""
        package = self.__package
        path = package.get_directory_name()
        package = package.get_parent()
        while package:
            path = package.get_directory_name() + "/" + path
            package = package.get_parent()
        return path
              
    def __on_click_browse(self):
        widget = CardSetPackageBrowserWidget(self.__package)
        widget.package_selected.connect(self.__on_card_set_package_selected)
        Config.app.push_gui_state(widget)
              
    def __on_card_set_package_selected(self, card_set_package: CardSetPackage):
        self.__package = card_set_package
        self.__edit_path.set_text(self.get_path())

    def __on_click_create(self):
        card_set = Config.app.card_database.create_card_set(
            name=self.__edit_display_name.get_text(),
            file_name=self.__edit_file_name.get_text(),
            package=self.__package)
        self.card_set_created.emit(card_set)
        self.close()

    def __on_click_cancel(self):
        self.canceled.emit()
        self.close()

    def __auto_set_file_name(self):
        name = self.__edit_display_name.get_text()
        file_name = name.lower().replace(" ", "_").replace("'", "")
        self.__edit_file_name.set_text(file_name)

    def __on_click_auto(self):
        auto = self.__checkbox_auto_file_name.is_checked()
        self.__edit_file_name.set_enabled(not auto)
        if auto:
            self.__auto_set_file_name()

    def __on_display_name_edited(self):
        if self.__checkbox_auto_file_name.is_checked():
            self.__auto_set_file_name()

