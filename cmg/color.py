

class Color:
    def __init__(self, r, g=None, b=None, a=None):
        if g is not None:
            self.r = r
            self.g = g
            self.b = b
            self.a = a if a is not None else 255
        elif isinstance(r, Color):
            self.r = r.r
            self.g = r.g
            self.b = r.b
            self.a = r.a if a is None else a
        elif isinstance(r, tuple) or isinstance(r, list):
            self.r = r[0]
            self.g = r[1]
            self.b = r[2]
            if a is not None:
                self.a = a
            elif len(r) == 4:
                self.a = r[3]
            else:
                self.a = 255
        else:
            self.r = r
            self.g = r
            self.b = r
            self.a = 255
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))
        self.a = max(0, min(255, self.a))

    def __repr__(self):
        return "Color({}, {}, {}, {})".format(
            self.r, self.g, self.b, self.a)

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a

    def __getitem__(self, index):
        return (self.r, self.g, self.b, self.a)[index]

    def __mul__(self, other):
        if isinstance(other, Color):
            return Color(int(self.r * other.r + 0.5),
                         int(self.g * other.g + 0.5),
                         int(self.b * other.b + 0.5),
                         int(self.a * other.a + 0.5))
        else:
            return Color(int(self.r * other + 0.5),
                         int(self.g * other + 0.5),
                         int(self.b * other + 0.5),
                         int(self.a * other + 0.5))

    def __add__(self, other):
        if isinstance(other, Color):
            return Color(self.r + other.r,
                         self.g + other.g,
                         self.b + other.b,
                         self.a + other.a)
        else:
            raise TypeError(other.__class__)


def make_gray(amount):
    return gray(amount)


def gray(amount):
    return Color(amount)


def rgb(red, green, blue):
    return Color(red, green, blue)


def rgba(red, green, blue, alpha):
    return Color(red, green, blue, alpha)


BLACK = rgb(0,   0,   0)
GRAY = rgb(128, 128, 128)
LIGHT_GRAY = rgb(192, 192, 192)
WHITE = rgb(255, 255, 255)
RED = rgb(255,   0,   0)
GREEN = rgb(0, 255,   0)
BLUE = rgb(0,   0, 255)
YELLOW = rgb(255, 255,   0)
CYAN = rgb(0, 255, 255)
MAGENTA = rgb(255,   0, 255)
TRANSPARENT = rgba(0, 0, 0, 0)