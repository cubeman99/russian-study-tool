import json
import os
import pygame
import time
import shutil
import cmg
from cmg import color
import cmg.logging
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_tool.card_set import *
from study_tool.config import Config
from study_tool.menu_state import MenuState
from study_tool.study_state import StudyState
from study_tool.card_list_state import CardListState
from study_tool.scheduler import ScheduleMode

DEAD_ZONE = 0.01

class StudyCardsApp(Application):

  def __init__(self):
    Config.logger = cmg.logging.create_logger("study_tool",
                                              stdout=True,
                                              level=cmg.logging.LogLevel.Info)

    self.title = "Russian"
    Application.__init__(self, title=self.title, width=800, height=600)
    
    pygame.joystick.init()
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()
    
    self.font_bar_text = pygame.font.Font(None, 30)

    self.clock = pygame.time.Clock()
    self.graphics = Graphics(self.screen)
    self.joystick_ready = False
    self.inputs = [
      Input(index=2, name="Middle", reversed=True, max=1, min=-1),
      Input(index=1, name="Left", reversed=True, max=1, min=-1),
      Input(index=3, name="Right", reversed=True, max=1, min=-1)]
    
    # Load all card data
    self.save_file_name = ".study_data.sav"
    self.root = load_card_package_directory(path="data", name="words")
    
    self.load()

    self.states = []
    self.push_state(MenuState(self.root))
    #self.push_study_state(self.root.card_sets[1], CardSide.Russian)
    #self.push_card_list_state(self.root.card_sets[1])

    self.input.bind(pygame.K_ESCAPE, pressed=self.quit)

  def pop_state(self):
    if len(self.states) == 1:
      self.quit()
    else:
      del self.states[-1]

  def push_state(self, state):
    state.app = self
    self.states.append(state)
    state.begin()

  def push_study_state(self, card_set, side, mode=ScheduleMode.Learning):
    self.push_state(StudyState(card_set, side=side, mode=mode))

  def push_card_list_state(self, card_set):
    self.push_state(CardListState(card_set))

  def draw_completion_bar(self, g, center_y, left, right, card_set):
    cards = []
    if isinstance(card_set, list):
      cards = card_set
    else:
      cards = list(card_set.cards)
    total_cards = len(cards)

    font = self.font_bar_text
    left_margin = g.measure_text("100%", font=font)[0] + 4
    right_margin = g.measure_text(str(total_cards), font=font)[0] + 4
    bar_height = g.measure_text("1", font=font)[1]
    bar_width = right - left - left_margin - right_margin
    top = center_y - (bar_height / 2)

    x = left + left_margin
    score = 0
    for level in range(Config.proficiency_levels, -1, -1):
      count = len([c for c in cards if c.proficiency_level == level])
      if count > 0:
        score += count * max(0, level - 1)
        level_width = int(round(bar_width * (float(count) / total_cards)))
        if x + level_width > left + left_margin + bar_width:
          level_width = (left + left_margin + bar_width) - x
        g.fill_rect(x, top, level_width, bar_height,
                    color=Config.proficiency_level_colors[level])
        x += level_width
    score /= float((Config.proficiency_levels - 1) * len(cards))
    score = int(round(score * 100))
    g.draw_text(left + left_margin - 4, center_y, text="{}%".format(score),
                color=color.BLACK, align=Align.MiddleRight, font=font)
    g.draw_text(right, center_y, text=str(total_cards),
                color=color.BLACK, align=Align.MiddleRight, font=font)
  
  def draw_text_box(self, text, x, y, width, height,
                    border_color=color.BLACK, border_width=2,
                    background_color=color.WHITE, text_color=color.BLACK):
    r = pygame.Rect(x, y, 0, 0)
    r.inflate_ip(width, height)
    self.graphics.fill_rect(r.x, r.y, r.width, r.height, color=background_color)
    self.graphics.draw_rect(r.x, r.y, r.width, r.height, thickness=2, color=border_color)
    self.graphics.draw_text(x, y, text, align=Align.Centered, color=text_color)
    
  @property
  def state(self):
    return self.states[-1]

  def save(self):
    path = os.path.join(self.root.path, self.save_file_name)
    Config.logger.debug("Saving study data to: " + path)
    state = self.root.serialize()
    temp_path = path + ".temp"
    with open(temp_path, "w", encoding="utf8") as f:
      json.dump(state, f, indent=2, sort_keys=True)
    shutil.move(temp_path, path)

  def load(self):
    path = os.path.join(self.root.path, self.save_file_name)
    Config.logger.info("Loading study data from: " + path)
    if os.path.isfile(path):
      with open(path, "r", encoding="utf8") as f:
        state = json.load(f)
        self.root.deserialize(state)

  def update(self, dt):
    if not self.joystick_ready:
      for axis in range(self.joystick.get_numaxes()):
        if self.joystick.get_axis(axis) != 0:
          self.joystick_ready = True
    if self.joystick_ready:
      for index, input in enumerate(self.inputs):
        input.update(self.joystick.get_axis(input.index))
        self.state.buttons[index].update(
          dt=dt,
          is_down=input.amount > DEAD_ZONE,
          is_pressed=input.amount > DEAD_ZONE and input.prev_amount <= DEAD_ZONE)

    self.state.process_input()
    self.state.update(dt)

  def draw(self):
    self.graphics.clear(color.WHITE)
    states_to_draw = []
    for state in reversed(self.states):
      states_to_draw.append(state)
      if not state.draw_state_below:
        break
    for state in reversed(states_to_draw):
      # TODO: fade background
      state.draw(self.graphics)
        

if __name__ == "__main__":
  app = StudyCardsApp()
  app.run()
