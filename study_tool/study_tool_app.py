import json
import pygame
import time
from cmg import color
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_tool.card_set import *
from study_tool.menu_state import MenuState
from study_tool.study_state import StudyState
from study_tool.card_list_state import CardListState

DEAD_ZONE = 0.01

class StudyCardsApp(Application):

  def __init__(self):
    self.title = "Russian"
    Application.__init__(self, title=self.title, width=800, height=600)
    
    pygame.joystick.init()
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()
    
    self.font_bar_text = pygame.font.Font(None, 30)

    self.clock = pygame.time.Clock()
    self.joystick_ready = False
    self.inputs = [
      Input(index=2, name="Middle", reversed=True, max=1, min=-1),
      Input(index=1, name="Left", reversed=True, max=1, min=-1),
      Input(index=3, name="Right", reversed=True, max=1, min=-1)]

    # Load all card data
    self.save_file_name = ".study_data.sav"
    self.root = load_card_package_directory(path="data", name="root")
    self.states = []
    self.push_state(MenuState(self.root))
    #self.push_study_state(self.root.card_sets[0], CardSide.Russian)
    #self.push_card_list_state(self.root.card_sets[0])

    self.graphics = Graphics(self.screen)
    self.load()
    
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

  def push_study_state(self, card_set, side):
    self.push_state(StudyState(card_set, side))

  def push_card_list_state(self, card_set):
    self.push_state(CardListState(card_set))

  def draw_completion_bar(self, g, center_y, left, right, card_set):
    cards = []
    if isinstance(card_set, CardSet):
      cards = list(card_set.cards)
    else:
      for cs in card_set.all_card_sets():
        cards += cs.cards
    total_cards = len(cards)
    marked_cards = len([c for c in cards if c.marked and c.encountered])
    unmarked_cards = len([c for c in cards if not c.marked and c.encountered])
    unseen_cards = len([c for c in cards if not c.encountered])
    percent = int(round((float(unmarked_cards) / total_cards) * 100))

    color_unmarked = color.GREEN
    color_marked = color.RED
    color_unseen = color.GRAY
    font = self.font_bar_text
    left_margin = g.measure_text("100%", font=font)[0] + 4
    right_margin = g.measure_text(str(total_cards), font=font)[0] + 4
    bar_height = g.measure_text("1", font=font)[1]
    bar_width = right - left - left_margin - right_margin
    top = center_y - (bar_height / 2)
    
    bar_width_unmarked = int(round(bar_width * float(unmarked_cards) / total_cards))
    bar_width_marked = int(round(bar_width * float(marked_cards + unmarked_cards) / total_cards))

    g.draw_text(left + left_margin - 4, center_y, text="{}%".format(percent),
                color=color.BLACK, align=Align.MiddleRight, font=font)
    g.draw_text(right, center_y, text=str(total_cards),
                color=color.BLACK, align=Align.MiddleRight, font=font)
    g.fill_rect(left + left_margin, top, bar_width, bar_height,
                color=color_unseen)
    g.fill_rect(left + left_margin, top, bar_width_marked, bar_height,
                color=color_marked)
    g.fill_rect(left + left_margin, top, bar_width_unmarked, bar_height,
                color=color_unmarked)

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
    state = self.root.serialize()
    path = os.path.join(self.root.path, self.save_file_name)
    with open(path, "w", encoding="utf8") as f:
      json.dump(state, f, indent=2, sort_keys=True)

  def load(self):
    path = os.path.join(self.root.path, self.save_file_name)
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
