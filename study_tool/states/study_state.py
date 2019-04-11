from enum import IntEnum
import os
import pygame
import random
import time
import cmg
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool.card import *
from study_tool.card_attributes import *
from study_tool.card_set import CardSet, CardSetPackage, StudySet
from study_tool.config import Config
from study_tool.russian.types import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.scheduler import Scheduler, ScheduleMode
from study_tool.states.state import State, Button
from study_tool.states.sub_menu_state import SubMenuState


class Row:

  def __init__(self, columns):
    self.columns = list(columns)

  def __getitem__(self, column_index):
    return self.columns[column_index]


class Table:

  def __init__(self, column_widths=None, row_height=20):
    self.rows = []
    self.column_widths = list(column_widths)
    self.row_height = row_height

  def add_row(self, columns):
    row = Row(columns)
    self.rows.append(row)

  def __getitem__(self, row_index):
    return self.rows[row_index]


class StudyParams:
  def __init__(self,
               random_side=False,
               random_form=False,
               shown_side=CardSide.English,
               mode=ScheduleMode.Learning):
    self.random_side = random_side
    self.random_form = random_form
    self.shown_side = shown_side
    self.mode = mode

class StudyState(State):
  def __init__(self,
               card_set: StudySet,
               params=StudyParams()):
    super().__init__()
    self.card_fonts = [pygame.font.Font(None, x) for x in range(16, 73, 4)]
    self.card_attribute_font = pygame.font.Font(None, 30)
    self.card_status_font = pygame.font.Font(None, 30)
    self.word_type_font = pygame.font.Font(None, 34)
    self.word_details_font = pygame.font.Font(None, 24)

    # Setudy settings
    self.card_set = card_set
    self.shown_side = CardSide.English
    self.params = params

    self.card = None
    self.revealed = False
    self.prompt_text = AccentedText()
    self.prompt_attributes = []
    self.reveal_attributes = []
    self.scheduler = None
    self.examples = []

  def begin(self):
    """Begin the state."""
    self.buttons[0] = Button("Reveal", self.reveal)
    self.buttons[1] = Button("Exit", self.pause)
    self.buttons[2] = Button("Next", self.next)

    self.scheduler = Scheduler(cards=self.card_set.cards,
                               mode=self.params.mode)
    self.seen_cards = []
    self.card = None
    self.revealed = False
    self.next_card()

  def switch_sides(self):
    self.params.shown_side = CardSide(1 - self.params.shown_side)
    self.shown_side = CardSide(1 - self.shown_side)
    
  def pause(self):
    other_side = CardSide(1 - self.shown_side)
    self.app.push_state(SubMenuState(
      "Pause",
      [("Resume", None),
       ("List", lambda: (self.app.pop_state(),
                         self.app.push_card_list_state(self.card_set))),
       ("Quiz " + other_side.name, self.switch_sides),
       ("Menu", self.app.pop_state),
       ("Exit", self.app.quit)]))

  def exit_to_menu(self):
    self.app.quit()

  def next(self):
    self.scheduler.mark(self.card, knew_it=True)
    self.app.save()
    self.next_card()
  
  def mark(self):
    """
    Mark the current card as "didn't know" then move to the next card.
    """
    self.scheduler.mark(self.card, knew_it=False)
    self.app.save()
    self.next_card()

  def get_random_russian_form(self, card: Card, word: Word):
    """Get a random form of a russian word."""
    if isinstance(word, Verb):
      odds = random.randint(1, 10)
      if odds <= 3:
        plurality = random.choice([pl for pl in Plurality])
        person = random.choice([p for p in Person])
        conjugation = word.get_non_past(plurality=plurality, person=person)
        attributes = [CardAttributes.NonPast,
                      PLURALITY_TO_ATTRIBUTE[plurality],
                      PERSON_TO_ATTRIBUTE[person]]
      elif odds <= 6:
        gender = random.choice([gender for gender in Gender] + [None])
        attributes = [CardAttributes.Past]
        if gender is not None:
          plurality = Plurality.Singular
          attributes.append(GENDER_TO_ATTRIBUTE[gender])
        else:
          plurality = Plurality.Plural
          attributes.append(CardAttributes.Plural)
        conjugation = word.get_past(plurality=plurality, gender=gender)
      else:
        conjugation = card.get_text(CardSide.Russian)
        attributes = [CardAttributes.Infinitive]
      return (conjugation, attributes)

    elif isinstance(word, Adjective):
      attributes = []
      gender = random.choice([gender for gender in Gender] + [None])
      if gender is not None:
        attributes.append(GENDER_TO_ATTRIBUTE[gender])
        plurality = Plurality.Singular
      else:
        plurality = Plurality.Plural
        attributes.append(CardAttributes.Plural)
      short = (word.has_short_form() and random.random() < 0.2)
      if short:
        attributes.append(CardAttributes.Short)
        declension = word.get_declension(
          gender=gender,
          plurality=plurality,
          short=True)
      else:
        case = random.choice([case for case in Case])
        attributes.append(CASE_TO_ATTRIBUTE[case])
        declension = word.get_declension(
          gender=gender,
          plurality=plurality,
          animate=True,
          case=case,
          short=False)
      return (declension, attributes)

    elif isinstance(word, Noun):
      case = random.choice([case for case in Case])
      plurality = random.choice([pl for pl in Plurality])
      attributes = [PLURALITY_TO_ATTRIBUTE[plurality],
                    CASE_TO_ATTRIBUTE[case]]
      return (word.get_declension(plurality=plurality, case=case), attributes)

    else:
      return (card.get_text(CardSide.Russian), [])

  def next_card(self):
    """
    Show the next card.
    """

    self.revealed = False
    self.buttons[0] = Button("Reveal", self.reveal)

    # Get the next card to show
    self.card = self.scheduler.next()
    if self.card is None:
      self.app.pop_state()
      Config.logger.info("No cards left to study!")
      return
    
    if self.params.random_side:
      self.shown_side = random.choice([CardSide.English, CardSide.Russian])
    else:
      self.shown_side = self.params.shown_side
    reveal_side = 1 - self.shown_side

    # Get word info associated with this card
    word = self.app.get_card_word_details(self.card)
    if word is not None:
      forms = word.get_all_forms()
    else:
      forms = self.card.russian.text

    if (self.params.random_form and self.shown_side == CardSide.Russian and
        word is not None):
      # Get a random form of the card's word
      self.prompt_attributes = []
      self.prompt_text, self.reveal_attributes = (
        self.get_random_russian_form(card=self.card, word=word))
      self.reveal_attributes += self.card.get_attributes(self.shown_side)
      self.reveal_text = self.card.get_text(reveal_side)
      self.reveal_attributes += self.card.get_attributes(reveal_side)
    else:
      self.prompt_text = self.card.get_text(self.shown_side)
      self.prompt_attributes = self.card.get_attributes(self.shown_side)
      self.reveal_text = self.card.get_text(reveal_side)
      self.reveal_attributes = self.card.get_attributes(reveal_side)

    self.examples = self.app.example_database.get_example_sentences(forms, count=7)

    Config.logger.info("Showing card: " + repr(self.prompt_text))

  def reveal(self):
    self.revealed = True
    self.buttons[0] = Button("Mark", self.mark)

  def draw_table(self, g: Graphics, x, y, table: Table,
                 font, text_color=color.BLACK):
    cy = y
    for row_index, row in enumerate(table):
      cx = x
      h = table.row_height
      for column_index, text in enumerate(row):
        w = table.column_widths[column_index]
        back_color = color.WHITE
        if text == self.prompt_text:
          back_color = color.YELLOW
        g.fill_rect(cx, cy, w + 1, h + 1, back_color)
        g.draw_rect(cx, cy, w + 1, h + 1, color.BLACK, 1)
        g.draw_text(cx + 6, cy + (h / 2),
                    text=AccentedText(text),
                    font=font,
                    color=text_color,
                    align=Align.MiddleLeft)
        cx += w
      cy += h

  def draw_attributes(self, g: Graphics, y, attributes: list):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    total_attr_width = 0
    attr_spacing = 16
    attributes = sorted(attributes, key=lambda x: x.name)
    # Measure the width of each attribute text
    for index, attr in enumerate(attributes):
      name = attr.name
      if attr in ATTRIBUTE_NAMES:
        name = ATTRIBUTE_NAMES[attr]
      w, h = g.measure_text(text=name, font=self.card_attribute_font)
      total_attr_width += w
      if index > 0:
        total_attr_width += attr_spacing
    # Draw each attribute
    ax = screen_center_x - (total_attr_width / 2)
    ay = y
    for attr in attributes:
      name = attr.name
      if attr in ATTRIBUTE_NAMES:
        name = ATTRIBUTE_NAMES[attr]
      w, h = g.measure_text(text=name, font=self.card_attribute_font)
      rect = pygame.Rect(ax, ay - h, w, h)
      rect.inflate_ip(8, 6)
      back_color = color.BLACK
      if attr in ATTRIBUTE_COLORS:
        back_color = ATTRIBUTE_COLORS[attr]
      g.fill_rect(rect, color=back_color)
      g.draw_text(ax, ay,
                  text=name,
                  font=self.card_attribute_font,
                  color=color.WHITE,
                  align=Align.BottomLeft)
      ax += w + attr_spacing

  def draw_top_proficiency_bar(self, g: Graphics, top_y, bar_height, bar_color):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    marked_overlay_color = bar_color * 0.7

    # Draw recent history (left)
    max_history_display_count = 10
    history_display_count = min(max_history_display_count,
                                len(self.card.history))
    history_box_size = 20
    padding = (self.proficiency_margin_height - history_box_size) // 2
    spacing = 3
    for index in range(0, history_display_count):
      marked = not self.card.history[index]
      t = index / (max_history_display_count * 1.2)
      c = cmg.math.lerp(marked_overlay_color, bar_color, t)
      x = padding + ((history_display_count - index - 1) *
                     (spacing + history_box_size))
      if marked:
        g.fill_rect(x, top_y + padding,
                    history_box_size, history_box_size,
                    color=c)
      else:
        g.draw_rect(x, top_y + padding,
                    history_box_size, history_box_size,
                    color=c)

    # Draw time since last encounter (right)
    g.draw_text(screen_width - 16, top_y + (bar_height // 2),
                text=self.card.elapsed_time_string(),
                align=Align.MiddleRight,
                color=marked_overlay_color,
                font=self.card_status_font)

    # Draw current and predicted history score (middle)
    score_fail = self.card.get_next_history_score(False)
    score = self.card.get_history_score()
    score_pass = self.card.get_next_history_score(True)
    g.draw_text(screen_center_x, top_y + (bar_height // 2),
                text="{:.4f} < {:.4f} > {:.4f}".format(score_fail, score, score_pass),
                align=Align.Centered,
                color=marked_overlay_color,
                font=self.card_status_font)

  def draw(self, g: Graphics):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2
    self.proficiency_margin_height = 32

    # Draw top/bottom proficiency bars
    if self.card.proficiency_level > 0:
      marked_state_color = math.lerp(Config.proficiency_level_colors[
        self.card.proficiency_level], color.WHITE, 0.7)
      g.fill_rect(0, self.margin_top, screen_width,
                  self.proficiency_margin_height,
                  color=marked_state_color)
      g.fill_rect(0, screen_height - self.margin_bottom - self.proficiency_margin_height,
                  screen_width, self.proficiency_margin_height,
                  color=marked_state_color)
      self.draw_top_proficiency_bar(g, self.margin_top,
                                    self.proficiency_margin_height,
                                    bar_color=marked_state_color)
        
    # Draw word type
    word_type_name = self.card.word_type.name
    g.draw_text(screen_center_x, self.margin_top + 32 + 16,
                text=word_type_name,
                font=self.word_type_font,
                color=cmg.color.GRAY,
                align=Align.TopCenter)

    # Draw card text and attributes
    card_font = g.get_font_to_fit(
      text=self.prompt_text, width=screen_width, fonts=self.card_fonts)
    g.draw_text(screen_center_x, screen_center_y - 50,
                text=self.prompt_text,
                font=card_font,
                color=Config.card_front_text_color,
                align=Align.Centered)
    self.draw_attributes(g, y=screen_center_y - 50 - 60,
                         attributes=self.prompt_attributes)
    if self.revealed:
      card_font = g.get_font_to_fit(
        text=self.reveal_text, width=screen_width, fonts=self.card_fonts)
      g.draw_text(screen_center_x, screen_center_y + 50,
                  text=self.reveal_text,
                  font=card_font,
                  color=Config.card_back_text_color,
                  align=Align.Centered)
      self.draw_attributes(g, y=screen_center_y + 50 + 60,
                           attributes=self.reveal_attributes)

    # Draw example sentences
    if self.revealed and len(self.examples) > 0:
      for index, (sentence, occurences) in enumerate(self.examples):
        g.draw_text(20, self.margin_top + self.proficiency_margin_height + 60 + index*20,
                    text=sentence,
                    font=self.word_details_font,
                    color=Config.card_back_text_color,
                    align=Align.TopLeft)
        for start, word in occurences:
          w, h = g.measure_text(sentence[:start-1], font=self.word_details_font)
          g.draw_text(20 + w, self.margin_top + self.proficiency_margin_height + 60 + index*20,
                      text=word,
                      font=self.word_details_font,
                      color=color.RED,
                      align=Align.TopLeft)



    # Draw word details
    if self.revealed and self.card.word is not None:
      if isinstance(self.card.word, Noun):
        noun = self.card.word
        present = Table(column_widths=(120, 180, 180), row_height=22)
        present.add_row(["Case", "Singular", "Plural"])
        for case in Case:
          present.add_row([case.name,
                           noun.get_declension(case=case, plurality=Plurality.Singular),
                           noun.get_declension(case=case, plurality=Plurality.Plural)])
        self.draw_table(g, table=present,
                        x=20, y=screen_height - self.margin_bottom - 50 - (22 * 7),
                        font=self.word_details_font,
                        text_color=color.BLACK)
      elif isinstance(self.card.word, Adjective):
        adj = self.card.word
        present = Table(column_widths=(120, 180, 180, 180, 180), row_height=22)
        present.add_row(["", "Masculine", "Neuter", "Femanine", "Plural"])
        for case in Case:
          present.add_row([case.name,
                          adj.get_declension(case=case, gender=Gender.Masculine),
                          adj.get_declension(case=case, gender=Gender.Neuter),
                          adj.get_declension(case=case, gender=Gender.Femanine),
                           adj.get_declension(case=case, plurality=Plurality.Plural)])
        present.add_row(["Short",
                          adj.get_declension(short=True, gender=Gender.Masculine),
                          adj.get_declension(short=True, gender=Gender.Neuter),
                          adj.get_declension(short=True, gender=Gender.Femanine),
                          adj.get_declension(short=True, plurality=Plurality.Plural)])
        self.draw_table(g, table=present,
                        x=20, y=screen_height - self.margin_bottom - 50 - (22 * 8),
                        font=self.word_details_font,
                        text_color=color.BLACK)
      elif isinstance(self.card.word, Verb):
        verb = self.card.word
        other_aspect = Aspect(1 - verb.aspect)

        present = Table(column_widths=(40, 160), row_height=22)
        title = "Present" if verb.aspect == Aspect.Imperfective else "Future"
        title += " Tense"
        present.add_row(["", title])
        for index, (plurality, person, pronoun) in enumerate([
          (Plurality.Singular, Person.First, "я"),
          (Plurality.Singular, Person.Second, "ты"),
          (Plurality.Singular, Person.Third, "он"),
          (Plurality.Plural, Person.First, "мы"),
          (Plurality.Plural, Person.Second, "вы"),
          (Plurality.Plural, Person.Third, "они")]):
          conjugation = verb.non_past[(plurality, person)]
          present.add_row([pronoun, conjugation])
        
        past = Table(column_widths=(50, 160), row_height=22)
        past.add_row(["", "Past Tense"])
        for index, (plurality, gender, pronoun) in enumerate([
          (Plurality.Singular, Gender.Masculine, "он"),
          (Plurality.Singular, Gender.Femanine, "она"),
          (Plurality.Singular, Gender.Neuter, "оно"),
          (Plurality.Plural, None, "они")]):
          conjugation = verb.past[(plurality, gender)]
          past.add_row([pronoun, conjugation])
        past.add_row(["imp1", verb.imperative[Plurality.Singular]])
        past.add_row(["imp2", verb.imperative[Plurality.Plural]])

        participles = Table(column_widths=(100, 160, 160), row_height=22)
        participles.add_row(["", "Present", "Past"])
        participles.add_row(["Active", 
                              verb.active_participles[Tense.Present],
                              verb.active_participles[Tense.Past]])
        participles.add_row(["Adverbial", 
                              verb.adverbial_participles[Tense.Present],
                              verb.adverbial_participles[Tense.Past]])
        participles.add_row(["Passive", 
                              verb.passive_participles[Tense.Present],
                              verb.passive_participles[Tense.Past]])
    
        self.draw_table(g, table=present,
                        x=20, y=screen_height - self.margin_bottom - 20 - (22 * 7),
                        font=self.word_details_font,
                        text_color=color.BLACK)
        counterparts = AccentedText("")
        for index, counterpart in enumerate(verb.counterparts):
          if index > 0:
            counterparts += ", "
          counterparts += counterpart
        y = screen_height - self.margin_bottom - 20 - (22 * 7) - 12
        g.draw_text(20, y - (25 * 2),
                    text=other_aspect.name + " counterparts: " + counterparts,
                    font=self.word_details_font,
                    color=Config.card_back_text_color,
                    align=Align.BottomLeft)
        g.draw_text(20, y - (25 * 1),
                    text=verb.infinitive + " -- " + verb.translation,
                    font=self.word_details_font,
                    color=Config.card_back_text_color,
                    align=Align.BottomLeft)
        g.draw_text(20, y - (25 * 0),
                    text=verb.info,
                    font=self.word_details_font,
                    color=Config.card_back_text_color,
                    align=Align.BottomLeft)
        self.draw_table(g, table=past,
                        x=240, y=screen_height - self.margin_bottom - 20 - (22 * 7),
                        font=self.word_details_font,
                        text_color=color.BLACK)
        self.draw_table(g, table=participles,
                        x=640, y=screen_height - self.margin_bottom - 20 - (22 * 4),
                        font=self.word_details_font,
                        text_color=color.BLACK)

    # Draw state
    State.draw(self, g)

    # Draw text at top
    g.draw_text(32, self.margin_top / 2,
                text=self.card_set.name,
                color=cmg.color.GRAY,
                align=Align.MiddleLeft)
    metrics = self.card_set.get_study_metrics()
    g.draw_text(screen_center_x, self.margin_top / 2,
                text="{:.0f} / {:.0f}".format(metrics.get_proficiency_count(),
                                              metrics.history_score),
                color=cmg.color.GRAY,
                align=Align.Centered)
    self.app.draw_completion_bar(g, self.margin_top / 2,
                                 screen_center_x + 80,
                                 screen_width - 32,
                                 [c for c in self.scheduler.get_all_cards()])
