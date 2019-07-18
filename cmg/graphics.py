import pygame
import time
from enum import IntFlag
from cmg import color
from study_tool.russian.word import *


class Align(IntFlag):
  """
  Text align bit flags.
  """
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
  MiddleLeft = Middle | Left
  MiddleRight = Middle | Right
  Centered = Center | Middle


class Graphics:
  """
  Class used to draw graphics.
  """

  def __init__(self, screen: pygame.Surface):
    self.screen = screen
    self.font = pygame.font.Font(None, 38)
    self.accent_input_chars = "'´`"
    self.accent_render_char = "´"
    self.accent_bitmap = {}

  def clear(self, color):
    self.screen.fill(tuple(color))
    
  #----------------------------------------------------------------------------
  # Shapes
  #----------------------------------------------------------------------------

  def draw_image(self, source, x, y):
    self.screen.blit(source=source, dest=(x, y))

  def draw_rect(self, x, y=None, width=None, height=None, color=color.BLACK, thickness=1):
    if isinstance(x, pygame.Rect):
      rect = x
    else:
      rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(self.screen, tuple(color), rect, thickness)

  def fill_rect(self, x, y=None, width=None, height=None, color=color.BLACK):
    if isinstance(x, pygame.Rect):
      rect = x
    else:
      rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(self.screen, tuple(color), rect, 0)

  #----------------------------------------------------------------------------
  # Text
  #----------------------------------------------------------------------------

  def measure_text(self, text, font=None):
    """
    Returns the width and height in pixels needed to render text with the
    given font.
    """
    if font is None:
      font = self.font
    text = AccentedText(text)
    return font.size(text.text)
    text_to_render = text
    for accent_char in self.accent_input_chars:
      text_to_render = text_to_render.replace(accent_char, "")
    return font.size(text_to_render)

  def get_font_to_fit(self, text, width: float,
                      fonts: list) -> pygame.font.Font:
    """
    Returns the largest font from a list of fonts that will allow the given
    text to fit within the specified width.
    """
    fonts = sorted(fonts, key=lambda font: font.get_height(), reverse=True)
    for font in fonts:
      w, h = self.measure_text(text=text, font=font)
      if w <= width:
        return font
    return font

  def draw_text(self, x, y, text, color=color.BLACK, font=None, align=Align.TopLeft, accented=True):
    """
    Draw accented text.
    """
    if accented:
      self.draw_accented_text(x, y, text, color, font=font, align=align)
    else:
      w, h = font.size(text)
      if Align.Center in align:
        x -= w / 2
      if Align.Middle in align:
        y -= h / 2
      if Align.Right in align:
        x -= w
      if Align.Bottom in align:
        y -= h

      # Draw text
      text_bitmap = font.render(text, True, tuple(color))
      self.screen.blit(text_bitmap, [x, y])

  def draw_accented_text(self, x, y, text, color=color.BLACK, font=None, align=Align.TopLeft):
    """
    Draw accented text.
    """
    if font is None:
      font = self.font
    if font not in self.accent_bitmap:
      self.accent_bitmap[font] = font.render(self.accent_render_char, True, tuple(color))
    self.accent_half_width = self.font.size(self.accent_render_char)[0] / 2
  
    text = AccentedText(text)
    w, h = font.size(text.text)
    if Align.Center in align:
      x -= w / 2
    if Align.Middle in align:
      y -= h / 2
    if Align.Right in align:
      x -= w
    if Align.Bottom in align:
      y -= h

    # Draw text
    text_bitmap = font.render(text.text, True, tuple(color))
    self.screen.blit(text_bitmap, [x, y])
    
    # Draw accent marks
    for accent_index in text.accents:
      w1, _ = font.size(text.text[:accent_index])
      w2, _ = font.size(text.text[:accent_index + 1])
      center_x = (w2 + w1) / 2
      self.screen.blit(self.accent_bitmap[font],
                        [x + center_x - self.accent_half_width, y])


# This is a simple class that will help us print to the self.screen
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 38)

    def print(self, screen, textString):
        textBitmap = self.font.render(textString, True, tuple(color.BLACK))
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
