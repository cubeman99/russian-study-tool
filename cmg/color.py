import pygame
import time
from enum import IntFlag

BLACK   = (  0,   0,   0)
GRAY    = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
WHITE   = (255, 255, 255)
RED     = (255,   0,   0)
GREEN   = (  0, 255,   0)
BLUE    = (  0,   0, 255)
YELLOW  = (255, 255,   0)
CYAN    = (  0, 255, 255)
MAGENTA = (255,   0, 255)

def make_gray(amount):
  return tuple([amount] * 3)
