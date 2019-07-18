import pygame
import time
import operator
from cmg.event import Event

Keys = pygame


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
          self.percent = min(1.0, (time.time() - self.start) / self.delay)
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
    self.key_pressed = Event(int, str)
    self.key_released = Event(int, str)

  def bind(self, key, pressed=None, released=None, down=None):
    bind = KeyBind(key, pressed=pressed, released=released, down=down)
    self.binds.append(bind)
    if key not in self.bind_dict:
      self.bind_dict[key] = []
    self.bind_dict[key].append(bind)
    return bind

  def update(self):
    for key in self.down_keys:
      if key in self.bind_dict:
        for bind in self.bind_dict[key]:
          if bind.down_callback is not None:
            bind.down_callback()

  def on_key_down(self, key, unicode):
    if key in self.bind_dict:
      for bind in self.bind_dict[key]:
        bind.down()
    self.down_keys.add(key)
    self.key_pressed.emit(key, unicode)
        
  def on_key_up(self, key):
    if key in self.bind_dict:
      for bind in self.bind_dict[key]:
        bind.up()
    self.down_keys.remove(key)
    self.key_released.emit(key)

