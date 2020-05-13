from enum import IntEnum
import os
import time
import cmg
import cmg.logging
from cmg.color import Color
from cmg.color import Colors

app = None

class Config:
    logger = None

    background_color = cmg.Theme.color_background
    window_border_color = cmg.Theme.color_outline
    window_border_thickness = 4

    #color_edit_invalid = Color(255, 200, 200)
    #color_edit_modified = Color(255, 255, 200)
    #color_edit_new = Color(200, 255, 200)

    #margin_top = 70
    #margin_bottom = 80
    #margin_color = color.make_gray(210)
    #margin_border_color = color.make_gray(150)
    #margin_border_thickness = 3
    #title_color = Color.BLACK

    color_edit_invalid = Color(80, 30, 30)
    color_edit_modified = Color(80, 80, 30)
    color_edit_new = Color(30, 80, 30)

    margin_top = 70
    margin_bottom = 80
    margin_color = cmg.Theme.color_background_light
    margin_border_color = cmg.Theme.color_background_light
    margin_border_thickness = 3
    title_color = cmg.Theme.color_text

    button_text_color = cmg.Theme.color_text
    button_background_color = cmg.Theme.color_background
    button_border_color = cmg.Theme.color_outline
    button_border_thickness = 2

    option_cursor_color = Colors.BLUE
    option_cursor_width = 16
    option_cursor_height = 6
    option_text_color = cmg.Theme.color_text
    option_background_colors = [cmg.Theme.color_background, cmg.Theme.color_background_light]
    option_border_colors = [cmg.Theme.color_background, cmg.Theme.color_background_light]
    option_highlighted_text_color = Colors.BLUE
    option_highlighted_background_color = cmg.Theme.color_background_highlighted
    option_highlighted_border_color = Colors.BLUE

    card_front_text_color = cmg.Theme.color_text
    card_back_text_color = cmg.Theme.color_text

    menu_cursor_speed = 10.0  # menu items per second

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
    proficiency_level_colors = {0: Colors.GRAY,
                                1: Colors.RED,
                                2: Color(255, 128, 0),
                                3: Colors.YELLOW,
                                4: Colors.GREEN}
    max_examples_to_display = 7
    

    # Dark
    proficiency_level_colors = {0: Color(100),
                                1: Color(128, 0, 0),
                                2: Color(128, 64, 0),
                                3: Color(128, 128, 0),
                                4: Color(0, 128, 0)}

if Config.logger is None:
    Config.logger = cmg.logging.create_logger("study_tool",
                                              stdout=True,
                                              level=cmg.logging.LogLevel.Info)
