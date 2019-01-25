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

class Align(IntFlag):
  Center = 0x1
  Left = 0x2
  Right = 0x4
  Bottom = 0x8
  Top = 0x10
  Middle = 0x20
  TopLeft = Top | Left
  TopRight = Top | Right
  TopCenter = Top | Center
  BottomLeft = Bottom | Left
  BottomRight = Bottom | Right
  BottomCenter = Bottom | Center
  Centered = Center | Middle

class Graphics:

  def __init__(self, screen):
    self.screen = screen
    self.font = pygame.font.Font(None, 38)
    self.accent_input_chars = "'´`"
    self.accent_render_char = "´"
    self.accent_bitmap = {}

  def draw_rect(self, x, y=None, width=None, height=None, color=BLACK, thickness=1):
    if isinstance(x, pygame.Rect):
      rect = x
    else:
      rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(self.screen, color, rect, thickness)

  def fill_rect(self, x, y=None, width=None, height=None, color=BLACK):
    if isinstance(x, pygame.Rect):
      rect = x
    else:
      rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(self.screen, color, rect, 0)

  def draw_text(self, x, y, text, color=BLACK, font=None, align=Align.TopLeft):
    if font is None:
      font = self.font
    if font not in self.accent_bitmap:
      self.accent_bitmap[font] = font.render(self.accent_render_char, True, BLACK)
    self.accent_half_width = self.font.size(self.accent_render_char)[0] / 2
    
    text_to_render = text
    for accent_char in self.accent_input_chars:
      text_to_render = text_to_render.replace(accent_char, "")
    
    w, h = font.size(text_to_render)
    if Align.Center in align:
      x -= w / 2
    if Align.Middle in align:
      y -= h / 2
    if Align.Right in align:
      x -= w
    if Align.Bottom in align:
      y -= h

    # Draw accent marks
    text_to_render = ""
    for index, c in enumerate(text):
      if c in self.accent_input_chars:
        w1, _ = font.size(text_to_render)
        w2, _ = font.size(text_to_render[:-1])
        center_x = (w2 + w1) / 2
        self.screen.blit(self.accent_bitmap[font],
                         [x + center_x - self.accent_half_width, y])
      else:
        text_to_render += c
    text_bitmap = font.render(text_to_render, True, color)
    self.screen.blit(text_bitmap, [x, y])

# This is a simple class that will help us print to the self.screen
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 38)

    def print(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height
        
    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 30
        
    def indent(self):
        self.x += 10
        
    def unindent(self):
        self.x -= 10
