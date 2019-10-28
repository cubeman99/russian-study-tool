import math

# Constants
E = math.e
PI = math.pi
TWO_PI = math.pi * 2
HALF_PI = math.pi / 2
QUARTER_PI = math.pi / 4
TAU = math.tau

# Functions
floor = math.floor
ceil = math.ceil
exp = math.exp
pow = math.pow
sqrt = math.sqrt
cos = math.cos
sin = math.sin
tan = math.tan
acos = math.acos
asin = math.asin
atan = math.atan
cosh = math.cosh
sinh = math.sinh
tanh = math.tanh

def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0

def lerp(a, b, t):
    return (a * (1.0 - t)) + (b * t)

def clamp(x, min_value, max_value):
    if x < min_value:
        return min_value
    if x > max_value:
        return max_value
    return x
