from enum import IntEnum
import os
import time
from cmg import color

class Config:
  background_color = color.WHITE
  window_border_color = color.BLACK
  window_border_thickness = 4

  margin_top = 70
  margin_bottom = 80
  margin_color = color.make_gray(210)
  margin_border_color = color.make_gray(150)
  margin_border_thickness = 3
  title_color = color.BLACK

  button_text_color = color.BLACK
  button_background_color = color.WHITE
  button_border_color = color.BLACK
  button_border_thickness = 2
  
  option_cursor_color = color.BLUE
  option_cursor_width = 16
  option_cursor_height = 6
  option_text_color = color.BLACK
  option_background_colors = [color.WHITE, color.gray(230)]
  option_border_colors = [color.gray(200), color.gray(200) * 0.75]
  option_highlighted_text_color = color.BLUE
  option_highlighted_background_color = color.rgb(200, 200, 255)
  option_highlighted_border_color = color.BLUE

  card_front_text_color = color.BLACK
  card_back_text_color = color.BLACK
