import math


def add(a, b):
    return a + b


def sub(a, b):
    return a - b


def mul(a, b):
    return a * b


def vec2_oper(op, self, other):
    if isinstance(other, Vec2) or isinstance(other, tuple):
        return Vec2(op(self.x, other.x), op(self.y, other.y))
    else:
        return Vec2(op(self.x, other), op(self.y, other))


class Vec2:
    def __init__(self, x, y=None):
        if y is None:
            self.x = x[0]
            self.y = x[1]
        else:
            self.x = x
            self.y = y

    def __add__(self, v):
        return vec2_oper(add, self, v)

    def __sub__(self, v):
        return vec2_oper(sub, self, v)

    def __mul__(self, v):
        return vec2_oper(mul, self, v)

    def __repr__(self):
        return "Vec2({}, {})".format(self.x, self.y)

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        else:
            self.y = value

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def distance(self, other):
        return math.sqrt((other - self).dot(other - self))

    def length(self):
        return math.sqrt(self.dot(self))

    def totuple(self) -> tuple:
        return (self.x, self.y)

