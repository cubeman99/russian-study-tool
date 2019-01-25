from enum import IntEnum
import os
import time
from cmg import color

class Config:
  margin_top = 70
  margin_bottom = 80
  margin_color = color.make_gray(210)
  margin_border_color = color.make_gray(150)
  margin_border_thickness = 3

  card_front_text_color = color.BLACK
  card_back_text_color = color.BLACK

  background_color = color.WHITE
  window_border_color = color.BLACK

  title_color = color.BLACK

  button_text_color = color.BLACK
  button_background_color = color.WHITE
  button_border_color = color.BLACK
  button_border_thickness = 2
