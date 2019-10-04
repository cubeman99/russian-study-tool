from pygame.rect import Rect
from cmg.graphics import Graphics
from cmg import color
from cmg.widgets import Widget
from cmg.widgets.layout import Layout
from cmg.math import Vec2


class Expandable2DArray:
    def __init__(self):
        self.__rows = {}

    def clear(self):
        self.__rows = {}

    def __getitem__(self, row: int, col: int):
        return self.get(row, col)

    def __setitem__(self, row: int, col: int, value):
        self.set(row, col, value)

    def __iter__(self):
        for _, columns in self.__rows.items():
            for _, item in columns.items():
                yield item

    def row_items(self, row: int):
        if row in self.__rows:
            for col, item in self.__rows[row].items():
                yield col, item

    def col_items(self, col: int):
        for row, columns in self.__rows.items():
            if col in columns:
                yield row, columns[col]

    def get(self, row: int, col: int, default=None):
        if row not in self.__rows:
            return default
        return self.__rows.get(col, default)

    def col_count(self) -> int:
        if not self.__rows:
            return 0
        return max(max(col.keys()) for _, col in self.__rows.items()) + 1

    def row_count(self) -> int:
        if not self.__rows:
            return 0
        return max(self.__rows.keys()) + 1

    def set(self, row: int, col: int, item):
        if row not in self.__rows:
            self.__rows[row] = {}
        self.__rows[row][col] = item

    def items(self):
        for row, columns in self.__rows.items():
            for col, item in columns.items():
                yield row, col, item

    def values(self):
        for row, columns in self.__rows.items():
            for col, item in columns.items():
                yield item

    def find(self, item):
        for row, col, temp in self.items():
            if temp == item:
                return row, col
        return None, None

    def remove(self, item):
        row, col = self.find(item)
        if row is not None:
            self.remove_at(row, col)

    def remove_at(self, row: int, col: int):
        if row in self.__rows and col in self.__rows[row]:
            del self.__rows[row][col]
            if not self.__rows[row]:
                del self.__rows[row]


class GridLayout(Layout):
    def __init__(self):
        super().__init__()
        self.__children = Expandable2DArray()
        self.__column_stretch_factors = {}
        self.__row_stretch_factors = {}

    def get_children(self) -> list:
        """Returns the list of children."""
        return list(self.__children.values())

    def set_column_stretch(self, col: int, stretch: float):
        self.__column_stretch_factors[col] = stretch

    def set_row_stretch(self, row: int, stretch: float):
        self.__row_stretch_factors[row] = stretch

    def add(self, item, row: int, col: int):
        """Adds a child to the grid."""
        assert item is not None
        if (row, col) in self.__children:
            self.__children.get(row, col).set_parent(None)
        self.__children.set(row, col, item)
        item.set_parent(self)

    def remove(self, child):
        """Removes a child."""
        child.set_parent(None)
        self.__children.remove(child)

    def remove_row(self, row: int, shift_up=False):
        """Removes an entire row."""
        row_items = list(self.__children.row_items(row))
        for col, child in row_items:
            child.set_parent(None)
            self.__children.remove_at(row, col)
        if shift_up:
            for row in range(row + 1, self.__children.row_count()):
                row_items = list(self.__children.row_items(row))
                for col, child in row_items:
                    self.__children.remove_at(row, col)
                    self.__children.set(row - 1, col, child)

    def remove_column(self, col: int, shift_left=False):
        """Removes an entire column."""
        col_items = list(self.__children.col_items(col))
        for row, child in col_items:
            child.set_parent(None)
            self.__children.remove_at(row, col)
        if shift_left:
            for col in range(col + 1, self.__children.col_count()):
                col_items = list(self.__children.col_items(col))
                for row, child in col_items:
                    self.__children.remove_at(row, col)
                    self.__children.set(row, col - 1, child)

    def clear(self):
        """Clears all children."""
        children = list(self.__children.values())
        for child in children:
            self.remove(child)

    def on_update(self):
        if not self.__children:
            return
        self.__update_axis_layout(0)
        self.__update_axis_layout(1)
        
    def calc_maximum_size(self) -> Vec2:
        """Calculate and return widget maximum sizes."""
        max_size = Vec2(0, 0)

        for child in self.get_children():
            child.calc_maximum_size()

        for row in range(self.__children.row_count()):
            row_max_height = self.DEFAULT_MAX_SIZE
            for col, child in self.__children.row_items(row):
                row_max_height = min(row_max_height, child.get_maximum_size().y)
            max_size.y += row_max_height

        for col in range(self.__children.col_count()):
            col_max_width = self.DEFAULT_MAX_SIZE
            for row, child in self.__children.col_items(col):
                col_max_width = min(col_max_width, child.get_maximum_size().x)
            max_size.x += col_max_width
            
        self.set_maximum_size(max_size)
        return max_size

    def calc_minimum_size(self) -> Vec2:
        """Calculate and return widget minimum sizes."""
        min_size = Vec2(0, 0)

        for child in self.get_children():
            child.calc_minimum_size()

        for row in range(self.__children.row_count()):
            row_min_height = 0
            for col, child in self.__children.row_items(row):
                row_min_height = max(row_min_height, child.get_minimum_size().y)
            min_size.y += row_min_height

        for col in range(self.__children.col_count()):
            col_min_width = 0
            for row, child in self.__children.col_items(col):
                col_min_width = max(col_min_width, child.get_minimum_size().x)
            min_size.x += col_min_width

        self.set_minimum_size(min_size)
        return min_size

    def __update_axis_layout(self, axis: int):
        size = self.get_size()
        child_size = self.get_size()[axis]
        stretch_space = size[axis]
        stretch_list = []

        stretch_factors = dict((self.__column_stretch_factors, self.__row_stretch_factors)[axis])
        sizes = {}
        min_sizes = {}
        max_sizes = {}

        count = (self.__children.col_count, self.__children.row_count)[axis]()
        cross_items = (self.__children.col_items, self.__children.row_items)[axis]

        for i in range(count):
            min_sizes[i] = 0
            max_sizes[i] = self.get_size()[axis]
            for _, child in self.__children.col_items(i):
                min_sizes[i] = max(min_sizes[i], child.get_minimum_size()[axis])
                max_sizes[i] = min(max_sizes[i], child.get_maximum_size()[axis])
            if i not in stretch_factors:
                stretch_factors[i] = 1
            if stretch_factors[i] > 0:
                stretch_list.append(i)
            else:
                sizes[i] = max(16, min_sizes[i])
                stretch_space -= sizes[i]
        
        # If all stretch factors are 0, then make them all 1
        if not stretch_list or sum(stretch_factors.values()) == 0:
            stretch_space = size[axis]
            for i in range(count):
                stretch_list.append(i)
                stretch_factors[i] = 1

        fits = False
        while not fits:
            fits = True
            stretch_sum = 0
            for i in stretch_list:
                stretch_sum += stretch_factors[i]

            if stretch_sum > 0:
                # Distribute sizes over the stretch space
                for i in stretch_list:
                    stretch = stretch_factors[i]
                    if stretch != 0:
                        sizes[i] = int(round(stretch_space * (stretch / stretch_sum)))

                # Clamp sizes
                stretch_list_index = 0
                while stretch_list_index < len(stretch_list):
                    i = stretch_list[stretch_list_index]
                    new_size = None
                    #if sizes[i] < min_sizes[i]:
                    #    new_size = min_sizes[i]
                    if sizes[i] > max_sizes[i]:
                        new_size = max_sizes[i]
                    if new_size is not None:
                        sizes[i] = new_size
                        del stretch_list[stretch_list_index]
                        stretch_space -= new_size
                        fits = False
                    else:
                        stretch_list_index += 1
        
        # Set final positions
        position = Vec2(self.get_rect().topleft)[axis]
        positions = {}
        for i in range(count):
            positions[i] = position
            for _, child in cross_items(i):
                rect = child.get_rect()
                pos = Vec2(rect.topleft)
                size = Vec2(rect.size)
                pos[axis] = position
                size[axis] = sizes[i]
                rect.topleft = pos.totuple()
                rect.size = size.totuple()
                child.set_rect(rect)
            position += sizes[i]

