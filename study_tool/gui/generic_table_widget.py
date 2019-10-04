from cmg import widgets
from cmg.color import Color
from cmg.event import Event
from study_tool.russian.word import AccentedText


class GenericTableRow:

    def __init__(self, item):
        self.item = item


class GenericTableColumn:
    def __init__(self, stretch=None):
        self.__stretch = stretch
    
    def get_stretch(self):
        return self.__stretch
    
    def set_stretch(self, stretch):
        self.__stretch = stretch
    
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
        label = widgets.Label(text)
        return label


class GenericTableWidget(widgets.Widget):
    """
    Generic table widget.
    """
    def __init__(self):
        super().__init__()
        self.__row_list = []
        self.__item_to_row_dict = {}
        self.__columns = []
        self.__grid_layout = widgets.GridLayout()
        self.set_layout(self.__grid_layout)

    def contains(self, item) -> bool:
        return item in self.__item_to_row_dict

    def get_row(self, item):
        return self.__item_to_row_dict.get(item, None)

    def get_items(self) -> list:
        return list(self.__item_to_row_dict.keys())

    def add_text_column(self, text_func, stretch=None):
        self.add_column(GenericTableTextColumn(text_func),
                        stretch=stretch)

    def add_button_column(self, text, callback, stretch=None):
        self.add_column(
            GenericTableButtonColumn(text=text, callback=callback),
            stretch=stretch)

    def add_column(self, column: GenericTableButtonColumn, stretch=None):
        index = len(self.__columns)
        self.__columns.append(column)
        if stretch is not None:
            column.set_stretch(stretch)
        self.__grid_layout.set_column_stretch(
            index, column.get_stretch())

    def clear(self):
        self.__grid_layout.clear()
        self.__row_list = []
        self.__item_to_row_dict = {}

    def add(self, item, enabled=True, color=None) -> GenericTableRow:
        if item in self.__item_to_row_dict:
            return self.__item_to_row_dict[item]
        
        # Create the row
        row_index = len(self.__row_list)
        row = GenericTableRow(item)
        for col_index, column in enumerate(self.__columns):
            widget = column.create(item)
            widget.set_enabled(enabled)
            self.__grid_layout.add(widget, row_index, col_index)
            if color:
                pass

        self.__row_list.append(row)
        self.__item_to_row_dict[item] = row
        return row

    def remove(self, item):
        assert item in self.__item_to_row_dict
        row = self.__item_to_row_dict[item]
        row_index = self.__row_list.index(row)
        del self.__item_to_row_dict[item]
        self.__row_list.remove(row)
        self.__grid_layout.remove_row(row_index, shift_up=True)

