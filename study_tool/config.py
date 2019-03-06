from enum import IntEnum
import os
import time
import cmg
import cmg.logging
from cmg import color

class Config:
  logger = None

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

  max_card_history_size = 100

  min_repeat_interval = 4
  proficiency_levels = 4  # 0 = new, 1 = hardest, 4 = easiest
  new_card_interval = 4
  proficiency_level_intervals = {1: 4,
                                 2: 8,
                                 3: 12,
                                 4: 16}
  proficiency_level_score_multiplier = {0: 0.0,
                                        1: 0.0,
                                        2: 0.25,
                                        3: 0.5,
                                        4: 1.0}
  proficiency_level_names = {1: "Hard",
                             2: "Medium",
                             3: "Easy",
                             4: "Learned"}
  proficiency_level_colors = {0: color.GRAY,
                              1: color.RED,
                              2: color.rgb(255, 128, 0),
                              3: color.YELLOW,
                              4: color.GREEN}
  
Config.logger = cmg.logging.create_logger("study_tool",
                                          stdout=True,
                                          level=cmg.logging.LogLevel.Info)
