from enum import IntEnum
from enum import IntFlag
import pygame
import time
import operator
from cmg.event import Event
from cmg.math import Vec2


class Keys(IntEnum):
    K_BACKSPACE  = pygame.K_BACKSPACE    # \b      backspace
    K_TAB        = pygame.K_TAB          # \t      tab
    K_CLEAR      = pygame.K_CLEAR        #         clear
    K_RETURN     = pygame.K_RETURN       # \r      return
    K_PAUSE      = pygame.K_PAUSE        #         pause
    K_ESCAPE     = pygame.K_ESCAPE       # ^[      escape
    K_SPACE      = pygame.K_SPACE        #         space
    K_EXCLAIM    = pygame.K_EXCLAIM      # !       exclaim
    K_DOUBLE_QUOTE = pygame.K_QUOTEDBL     # "       quotedbl
    K_POUND        = pygame.K_HASH         # #       hash
    K_DOLLAR     = pygame.K_DOLLAR       # $       dollar
    K_AMPERSAND  = pygame.K_AMPERSAND    # &       ampersand
    K_QUOTE      = pygame.K_QUOTE        #         quote
    K_OPEN_PAREN  = pygame.K_LEFTPAREN    # (       left parenthesis
    K_CLOSE_PAREN = pygame.K_RIGHTPAREN   # )       right parenthesis
    K_ASTERISK   = pygame.K_ASTERISK     # *       asterisk
    K_PLUS       = pygame.K_PLUS         # +       plus sign
    K_COMMA      = pygame.K_COMMA        # ,       comma
    K_MINUS      = pygame.K_MINUS        # -       minus sign
    K_PERIOD     = pygame.K_PERIOD       # .       period
    K_SLASH      = pygame.K_SLASH        # /       forward slash
    K_0          = pygame.K_0            # 0       0
    K_1          = pygame.K_1            # 1       1
    K_2          = pygame.K_2            # 2       2
    K_3          = pygame.K_3            # 3       3
    K_4          = pygame.K_4            # 4       4
    K_5          = pygame.K_5            # 5       5
    K_6          = pygame.K_6            # 6       6
    K_7          = pygame.K_7            # 7       7
    K_8          = pygame.K_8            # 8       8
    K_9          = pygame.K_9            # 9       9
    K_COLON      = pygame.K_COLON        # :       colon
    K_SEMICOLON  = pygame.K_SEMICOLON    # ;       semicolon
    K_LESS       = pygame.K_LESS         # <       less-than sign
    K_EQUALS     = pygame.K_EQUALS       # =       equals sign
    K_GREATER    = pygame.K_GREATER      # >       greater-than sign
    K_QUESTION   = pygame.K_QUESTION     # ?       question mark
    K_AT         = pygame.K_AT           # @       at
    K_OPEN_BRACK  = pygame.K_LEFTBRACKET  # [       left bracket
    K_BACKSLASH   = pygame.K_BACKSLASH    # \       backslash
    K_CLOSE_BRACK = pygame.K_RIGHTBRACKET #  ]      right bracket
    K_CARET       = pygame.K_CARET        # ^       caret
    K_UNDERSCORE = pygame.K_UNDERSCORE   # _       underscore
    K_BACKQUOTE  = pygame.K_BACKQUOTE    # `       grave
    K_A          = pygame.K_a            # a       a
    K_B          = pygame.K_b            # b       b
    K_C          = pygame.K_c            # c       c
    K_D          = pygame.K_d            # d       d
    K_E          = pygame.K_e            # e       e
    K_F          = pygame.K_f            # f       f
    K_G          = pygame.K_g            # g       g
    K_H          = pygame.K_h            # h       h
    K_I          = pygame.K_i            # i       i
    K_J          = pygame.K_j            # j       j
    K_K          = pygame.K_k            # k       k
    K_L          = pygame.K_l            # l       l
    K_M          = pygame.K_m            # m       m
    K_N          = pygame.K_n            # n       n
    K_O          = pygame.K_o            # o       o
    K_P          = pygame.K_p            # p       p
    K_Q          = pygame.K_q            # q       q
    K_R          = pygame.K_r            # r       r
    K_S          = pygame.K_s            # s       s
    K_T          = pygame.K_t            # t       t
    K_U          = pygame.K_u            # u       u
    K_V          = pygame.K_v            # v       v
    K_W          = pygame.K_w            # w       w
    K_X          = pygame.K_x            # x       x
    K_Y          = pygame.K_y            # y       y
    K_Z          = pygame.K_z            # z       z
    K_DELETE     = pygame.K_DELETE       #         delete
    K_KP0        = pygame.K_KP0          #         keypad 0
    K_KP1        = pygame.K_KP1          #         keypad 1
    K_KP2        = pygame.K_KP2          #         keypad 2
    K_KP3        = pygame.K_KP3          #         keypad 3
    K_KP4        = pygame.K_KP4          #         keypad 4
    K_KP5        = pygame.K_KP5          #         keypad 5
    K_KP6        = pygame.K_KP6          #         keypad 6
    K_KP7        = pygame.K_KP7          #         keypad 7
    K_KP8        = pygame.K_KP8          #         keypad 8
    K_KP9        = pygame.K_KP9          #         keypad 9
    K_KP_PERIOD  = pygame.K_KP_PERIOD    # .       keypad period
    K_KP_DIVIDE  = pygame.K_KP_DIVIDE    # /       keypad divide
    K_KP_MULTIPL = pygame.K_KP_MULTIPLY  # *       keypad multiply
    K_KP_MINUS   = pygame.K_KP_MINUS     # -       keypad minus
    K_KP_PLUS    = pygame.K_KP_PLUS      # +       keypad plus
    K_KP_ENTER   = pygame.K_KP_ENTER     # \r      keypad enter
    K_KP_EQUALS  = pygame.K_KP_EQUALS    # =       keypad equals
    K_UP         = pygame.K_UP           #         up arrow
    K_DOWN       = pygame.K_DOWN         #         down arrow
    K_RIGHT      = pygame.K_RIGHT        #         right arrow
    K_LEFT       = pygame.K_LEFT         #         left arrow
    K_INSERT     = pygame.K_INSERT       #         insert
    K_HOME       = pygame.K_HOME         #         home
    K_END        = pygame.K_END          #         end
    K_PAGEUP     = pygame.K_PAGEUP       #         page up
    K_PAGEDOWN   = pygame.K_PAGEDOWN     #         page down
    K_F1         = pygame.K_F1           #         F1
    K_F2         = pygame.K_F2           #         F2
    K_F3         = pygame.K_F3           #         F3
    K_F4         = pygame.K_F4           #         F4
    K_F5         = pygame.K_F5           #         F5
    K_F6         = pygame.K_F6           #         F6
    K_F7         = pygame.K_F7           #         F7
    K_F8         = pygame.K_F8           #         F8
    K_F9         = pygame.K_F9           #         F9
    K_F10        = pygame.K_F10          #         F10
    K_F11        = pygame.K_F11          #         F11
    K_F12        = pygame.K_F12          #         F12
    K_F13        = pygame.K_F13          #         F13
    K_F14        = pygame.K_F14          #         F14
    K_F15        = pygame.K_F15          #         F15
    K_NUMLOCK    = pygame.K_NUMLOCK      #         numlock
    K_CAPSLOCK   = pygame.K_CAPSLOCK     #         capslock
    K_SCROLLOCK  = pygame.K_SCROLLOCK    #         scrollock
    K_RSHIFT     = pygame.K_RSHIFT       #         right shift
    K_LSHIFT     = pygame.K_LSHIFT       #         left shift
    K_RCTRL      = pygame.K_RCTRL        #         right control
    K_LCTRL      = pygame.K_LCTRL        #         left control
    K_RALT       = pygame.K_RALT         #         right alt
    K_LALT       = pygame.K_LALT         #         left alt
    K_RMETA      = pygame.K_RMETA        #         right meta
    K_LMETA      = pygame.K_LMETA        #         left meta
    K_LSUPER     = pygame.K_LSUPER       #         left Windows key
    K_RSUPER     = pygame.K_RSUPER       #         right Windows key
    K_MODE       = pygame.K_MODE         #         mode shift
    K_HELP       = pygame.K_HELP         #         help
    K_PRINT      = pygame.K_PRINT        #         print screen
    K_SYSREQ     = pygame.K_SYSREQ       #         sysrq
    K_BREAK      = pygame.K_BREAK        #         break
    K_MENU       = pygame.K_MENU         #         menu
    K_POWER      = pygame.K_POWER        #         power
    K_EURO       = pygame.K_EURO         #         Euro


class KeyMods(IntFlag):
    NONE = pygame.KMOD_NONE      # no modifier keys pressed
    LSHIFT = pygame.KMOD_LSHIFT  # left shift
    RSHIFT = pygame.KMOD_RSHIFT  # right shift
    SHIFT = pygame.KMOD_SHIFT    # left shift or right shift or both
    LCTRL = pygame.KMOD_LCTRL    # left control
    RCTRL = pygame.KMOD_RCTRL    # right control
    CTRL = pygame.KMOD_CTRL      # left control or right control or both
    LALT = pygame.KMOD_LALT      # left alt
    RALT = pygame.KMOD_RALT      # right alt
    ALT = pygame.KMOD_ALT        # left alt or right alt or both
    LMETA = pygame.KMOD_LMETA    # left meta
    RMETA = pygame.KMOD_RMETA    # right meta
    META = pygame.KMOD_META      # left meta or right meta or both
    CAPS = pygame.KMOD_CAPS      # caps lock
    NUMLOCK = pygame.KMOD_NUM    # num lock
    MODE = pygame.KMOD_MODE      # mode


class MouseButtons(IntEnum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5


class KeyShortcut:

    MOD_NAMES = {
        "ctrl": KeyMods.LCTRL,
        "shift": KeyMods.LSHIFT,
        "alt": KeyMods.LALT,
        "meta": KeyMods.META,
        "win": KeyMods.META,
        "caps": KeyMods.CAPS,
        "num": KeyMods.NUMLOCK,
        "mode": KeyMods.MODE,
        }

    KEY_NAMES = {
        "left": Keys.K_LEFT,
        "right": Keys.K_RIGHT,
        "up": Keys.K_UP,
        "down": Keys.K_DOWN,
        "home": Keys.K_HOME,
        "end": Keys.K_END,
        "insert": Keys.K_INSERT,
        "ins": Keys.K_INSERT,
        "delete": Keys.K_DELETE,
        "del": Keys.K_DELETE,
        "pageup": Keys.K_PAGEUP,
        "pagedown": Keys.K_PAGEDOWN,
        "pgup": Keys.K_PAGEUP,
        "pgdown": Keys.K_PAGEDOWN,
        "space": Keys.K_SPACE,
        "enter": Keys.K_SPACE,
        "return": Keys.K_RETURN,
        "ret": Keys.K_RETURN,
        "escape": Keys.K_ESCAPE,
        "esc": Keys.K_ESCAPE,
        ";": Keys.K_SEMICOLON,
        ".": Keys.K_PERIOD,
        ",": Keys.K_COMMA,
        "[": Keys.K_OPEN_BRACK,
        "]": Keys.K_CLOSE_BRACK,
        "-": Keys.K_MINUS,
        "=": Keys.K_EQUALS,
        "'": Keys.K_QUOTE,
        "/": Keys.K_SLASH,
        "0": Keys.K_0,
        "1": Keys.K_1,
        "2": Keys.K_2,
        "3": Keys.K_3,
        "4": Keys.K_4,
        "5": Keys.K_5,
        "6": Keys.K_6,
        "7": Keys.K_7,
        "8": Keys.K_8,
        "9": Keys.K_9,
        "f1": Keys.K_F1,
        "f2": Keys.K_F2,
        "f3": Keys.K_F3,
        "f4": Keys.K_F4,
        "f5": Keys.K_F5,
        "f6": Keys.K_F6,
        "f7": Keys.K_F7,
        "f8": Keys.K_F8,
        "f9": Keys.K_F9,
        "f10": Keys.K_F10,
        "f11": Keys.K_F11,
        "f12": Keys.K_F12,
        "f13": Keys.K_F13,
        "f14": Keys.K_F14,
        "f15": Keys.K_F15,
        "a": Keys.K_A,
        "b": Keys.K_B,
        "c": Keys.K_C,
        "d": Keys.K_D,
        "e": Keys.K_E,
        "f": Keys.K_F,
        "g": Keys.K_G,
        "h": Keys.K_H,
        "i": Keys.K_I,
        "j": Keys.K_J,
        "k": Keys.K_K,
        "l": Keys.K_L,
        "m": Keys.K_M,
        "n": Keys.K_N,
        "o": Keys.K_O,
        "p": Keys.K_P,
        "q": Keys.K_Q,
        "r": Keys.K_R,
        "s": Keys.K_S,
        "y": Keys.K_Y,
        "u": Keys.K_U,
        "v": Keys.K_V,
        "w": Keys.K_W,
        "x": Keys.K_X,
        "y": Keys.K_Y,
        "z": Keys.K_Z,
        }

    def __init__(self, pattern: str, callback=None):
        if isinstance(pattern, KeyShortcut):
            self.__keys = set(pattern.__keys)
            self.__mods = pattern.__mods
            self.__callback = callback if callback else pattern.callback
        else:
            self.__keys = set()
            self.__mods = KeyMods.NONE
            self.__callback = callback
            tokens = [x.strip().lower() for x in pattern.split("+")]
            for token in tokens:
                if token in self.MOD_NAMES:
                    self.__mods |= self.MOD_NAMES[token]
                if token in self.KEY_NAMES:
                    self.__keys.add(self.KEY_NAMES[token])

    def invoke(self):
        if self.__callback:
            self.__callback()

    def get_callback(self):
        return self.__callback

    def matches(self, key, mods):
        if self.__keys and key not in self.__keys:
            return False
        return mods == self.__mods


class Input:
    def __init__(self, index, name, reversed=False, min=0, max=1):
        self.amount = 0
        self.prev_amount = 0
        self.index = index
        self.name = name
        self.reversed = reversed
        self.min = min
        self.max = max

    def get_amount(self):
        return self.amount

    def update(self, amount):
        self.prev_amount = self.amount
        self.amount = (amount - self.min) / (self.max - self.min)
        if self.reversed:
            self.amount = 1 - self.amount


class Condition:
    def __or__(self, other):
        return GestureCondition(op=operator.or_, left=self, right=other)

    def __and__(self, other):
        return GestureCondition(op=operator.and_, left=self, right=other)

    def __invert__(self):
        return GestureNotCondition(self)


class GestureCondition(Condition):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return "{} {} {}".format(repr(self.left), self.op.__name__, repr(self.right))

    def eval(self, **kwargs):
        return self.op(self.left.eval(**kwargs), self.right.eval(**kwargs))


class GestureNotCondition(Condition):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "not " + repr(self.value)

    def eval(self, **kwargs):
        return not self.value.eval(**kwargs)


class KeyBind:
    def __init__(self, key, down=None, pressed=None, released=None):
        self.key = key
        self.down_callback = down
        self.pressed_callback = pressed
        self.released_callback = released
        self.is_down = False

    def down(self):
        if not self.is_down:
            self.is_down = True
            if self.pressed_callback is not None:
                self.pressed_callback()

    def up(self):
        if self.is_down:
            self.is_down = False
            if self.released_callback is not None:
                self.released_callback()


class InputBind(Condition):
    def __init__(self, input, min, max=None, reversed=False):
        self.input = input
        self.min = min
        self.max = max
        self.reversed = reversed

    def update(self):
        pass

    def __repr__(self):
        return "<{}>".format(self.input.name)

    def is_pressed(self):
        curr = self.input.amount
        prev = self.input.prev_amount
        if self.reversed:
            curr = 1 - curr
            prev = 1 - prev
        return curr >= self.min and prev < self.min

    def is_released(self):
        curr = self.input.amount
        prev = self.input.prev_amount
        if self.reversed:
            curr = 1 - curr
            prev = 1 - prev
        return curr < self.min and prev >= self.min

    def eval(self, **kwargs):
        curr = self.input.amount
        if self.reversed:
            curr = 1 - curr
        if "min" in kwargs and kwargs["min"] is True:
            return curr >= self.min
        return self.is_down()

    def is_down(self):
        curr = self.input.amount
        if self.reversed:
            curr = 1 - curr
        return curr >= self.min and (self.max is None or curr < self.max)


class Gesture(Condition):
    def __init__(self, bind, name, exclude=None, callback=None, delay=0):
        self.bind = bind
        self.exclude = exclude
        self.name = name
        self.start = None
        self.delay = delay
        self.pressed = False
        self.released = False
        self.callback = callback
        self.down = False
        self.reset = False
        self.percent = None

    def eval(self, **kwargs):
        return self.bind.eval(**kwargs)

    def clear(self):
        self.reset = True
        self.pressed = False

    def update(self):
        self.pressed = False
        self.released = False
        self.down = self.eval()
        self.percent = None

        if self.start is not None:
            if self.reset:
                if not self.eval(min=True):
                    self.start = None
                    self.released = True
                    self.reset = False
            elif self.exclude is not None and self.exclude.eval(min=True):
                self.reset = True
            elif self.down:
                if self.delay > 0.0:
                    self.percent = min(
                        1.0, (time.time() - self.start) / self.delay)
                if time.time() - self.start >= self.delay:
                    self.pressed = True
                    self.reset = True
                    if self.callback is not None:
                        self.callback()
                    print("Gesture '{}' pressed!".format(self.name))
            else:
                self.reset = True
        elif self.eval(min=True):
            self.start = time.time()

    def is_pressed(self):
        return self.pressed

    def is_released(self):
        return self.released

    def is_down(self):
        return self.down


class InputManager:
    def __init__(self):
        self.binds = []
        self.bind_dict = {}
        self.down_keys = set()
        self.key_pressed = Event(Keys, KeyMods, str)
        self.key_released = Event(Keys, KeyMods)
        self.mouse_pressed = Event(Vec2, MouseButtons)
        self.mouse_released = Event(Vec2, MouseButtons)
        self.__key_mods = KeyMods.NONE

    def bind(self, key, pressed=None, released=None, down=None):
        bind = KeyBind(key, pressed=pressed, released=released, down=down)
        self.binds.append(bind)
        if key not in self.bind_dict:
            self.bind_dict[key] = []
        self.bind_dict[key].append(bind)
        return bind

    def update(self):
        self.__key_mods = KeyMods(pygame.key.get_mods())
        for key in self.down_keys:
            if key in self.bind_dict:
                for bind in self.bind_dict[key]:
                    if bind.down_callback is not None:
                        bind.down_callback()

    def get_key_mods(self) -> KeyMods:
        return self.__key_mods
       
    def on_key_down(self, key, mod, unicode):
        if key in self.bind_dict:
            for bind in self.bind_dict[key]:
                bind.down()
        self.down_keys.add(key)
        self.key_pressed.emit(key, mod, unicode)

    def on_key_up(self, key, mod):
        if key in self.bind_dict:
            for bind in self.bind_dict[key]:
                bind.up()
        self.down_keys.remove(key)
        self.key_released.emit(key, mod)

    def on_mouse_down(self, pos, button):
        self.mouse_pressed.emit(pos, button)

    def on_mouse_up(self, pos, button):
        self.mouse_released.emit(pos, button)