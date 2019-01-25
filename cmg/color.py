import pygame
import time
from enum import IntFlag

class Color:
  def __init__(self, r, g=None, b=None):
    if g is not None:
      self.r = r
      self.g = g
      self.b = b
    elif isinstance(r, Color):
      self.r = r.r
      self.g = r.g
      self.b = r.b
    elif isinstance(r, tuple) or isinstance(r, list):
      self.r = r[0]
      self.g = r[1]
      self.b = r[2]
    else:
      self.r = r
      self.g = r
      self.b = r

  def __iter__(self):
    yield self.r
    yield self.g
    yield self.b

  def __getitem__(self, index):
    return (self.r, self.g, self.b)[index]

  def __mul__(self, other):
    if isinstance(other, Color):
      return Color(int(self.r * other.r + 0.5),
                   int(self.g * other.g + 0.5),
                   int(self.b * other.b + 0.5))
    else:
      return Color(int(self.r * other + 0.5),
                   int(self.g * other + 0.5),
                   int(self.b * other + 0.5))

def make_gray(amount):
  return gray(amount)

def gray(amount):
  return Color(amount)

def rgb(red, green, blue):
  return Color(red, green, blue)

BLACK      = rgb(  0,   0,   0)
GRAY       = rgb(128, 128, 128)
LIGHT_GRAY = rgb(192, 192, 192)
WHITE      = rgb(255, 255, 255)
RED        = rgb(255,   0,   0)
GREEN      = rgb(  0, 255,   0)
BLUE       = rgb(  0,   0, 255)
YELLOW     = rgb(255, 255,   0)
CYAN       = rgb(  0, 255, 255)
MAGENTA    = rgb(255,   0, 255)
