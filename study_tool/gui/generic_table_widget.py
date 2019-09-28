from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.russian.word import AccentedText


class GenericTableRow(widgets.Widget):

    def __init__(self, item, select_text="Select", enabled=True):
        super().__init__()
        self.item = item


class GenericTableColumn:
    def __init__(self, stretch=None):
        self.__stretch = stretch
    
    def get_stretch(self):
        return self.__stretch
    
    def create(self, item):
        return None


class GenericTableButtonColumn(GenericTableColumn):
    def __init__(self, text, callback):
        GenericTableColumn.__init__(self, stretch=0)
        self.__text = text
        self.__callback = callback

    def create(self, item):
        text = AccentedText(self.__text).text
        button = widgets.Button(text)
        button.clicked.connect(lambda: self.__callback(item))
        return button
        

class GenericTableTextColumn(GenericTableColumn):
    def __init__(self, text_func):
        GenericTableColumn.__init__(self, stretch=1)
        self.__text_func = text_func

    def create(self, item):
        text = AccentedText(self.__text_func(item)).text
        label = widgets.TextEdit(text)
        return label


class GenericTableWidget(widgets.Widget):
    """
    Generic table widget.
    """
    def __init__(self):
        super().__init__()
        self.__item_to_row_dict = {}
        self.__columns = []
        self.__layout_rows = widgets.VBoxLayout()
        self.set_layout(self.__layout_rows)

    def get_row(self, item):
        return self.__item_to_row_dict.get(item, None)

    def get_items(self) -> list:
        return list(self.__item_to_row_dict.keys())

    def add_text_column(self, text_func):
        column = GenericTableTextColumn(text_func)
        self.__columns.append(column)

    def add_button_column(self, text, callback):
        column = GenericTableButtonColumn(text=text, callback=callback)
        self.__columns.append(column)

    def clear(self):
        self.__layout_rows.clear()
        self.__item_to_row_dict = {}

    def add(self, item, enabled=True) -> GenericTableRow:
        if item in self.__item_to_row_dict:
            return self.__item_to_row_dict[item]
        
        # Create the row
        row = GenericTableRow(item, enabled=enabled)
        layout = widgets.HBoxLayout()
        for column in self.__columns:
            widget = column.create(item)
            layout.add_widget(widget, stretch=column.get_stretch())
        row.set_layout(layout)

        self.__layout_rows.add(row)
        self.__item_to_row_dict[item] = row
        return row

    def remove(self, item):
        row = self.__item_to_row_dict[item]
        self.__layout_rows.remove(row)
        del self.__item_to_row_dict[item]

