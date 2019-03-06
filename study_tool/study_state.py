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
from study_tool.card_set import CardSet, CardSetPackage
from study_tool.config import Config
from study_tool.russian.types import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.scheduler import Scheduler, ScheduleMode
from study_tool.state import State, Button
from study_tool.sub_menu_state import SubMenuState


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



class StudyState(State):
  def __init__(self, card_set,
               side=CardSide.English,
               mode=ScheduleMode.Learning):
    super().__init__()
    self.card_font = pygame.font.Font(None, 72)
    self.card_attribute_font = pygame.font.Font(None, 30)
    self.card_status_font = pygame.font.Font(None, 30)
    self.word_type_font = pygame.font.Font(None, 34)
    self.word_details_font = pygame.font.Font(None, 24)
    self.card_set = card_set
    self.shown_side = side
    self.hidden_side = CardSide(1 - side)
    self.card = None
    self.revealed = False
    self.scheduler = None
    self.mode = mode

  def begin(self):
    self.buttons[0] = Button("Reveal", self.reveal)
    self.buttons[1] = Button("Exit", self.pause)
    self.buttons[2] = Button("Next", self.next)

    self.scheduler = Scheduler(cards=self.card_set.cards, mode=self.mode)
    self.seen_cards = []
    self.card = None
    self.revealed = False
    self.next_card()

  def switch_sides(self):
    self.shown_side = CardSide(1 - self.shown_side)
    self.hidden_side = CardSide(1 - self.shown_side)
    
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
    self.scheduler.mark(self.card, knew_it=False)
    self.app.save()
    self.next_card()

  def next_card(self):
    self.revealed = False
    self.buttons[0] = Button("Reveal", self.reveal)
    self.card = self.scheduler.next()
    if self.card is None:
      self.app.pop_state()
      Config.logger.info("No cards left to study!")
    else:
      Config.logger.info("Showing card: " + self.card.text[self.shown_side])
      self.app.get_card_word_details(self.card)

  def reveal(self):
    self.revealed = True
    self.buttons[0] = Button("Mark", self.mark)

  def draw_table(self, g: Graphics, x, y, table: Table, font, text_color=color.BLACK):
    cy = y
    for row_index, row in enumerate(table):
      cx = x
      h = table.row_height
      for column_index, text in enumerate(row):
        w = table.column_widths[column_index]
        g.fill_rect(cx, cy, w + 1, h + 1, color.WHITE)
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


  def draw(self, g: Graphics):
    screen_width, screen_height = self.app.screen.get_size()
    screen_center_x = screen_width / 2
    screen_center_y = screen_height / 2

    if self.card.proficiency_level > 0:
      marked_state_color = math.lerp(Config.proficiency_level_colors[
        self.card.proficiency_level], color.WHITE, 0.7)
      g.fill_rect(0, self.margin_top, screen_width, 32,
                  color=marked_state_color)
      g.fill_rect(0, screen_height - self.margin_bottom - 32,
                  screen_width, 32,
                  color=marked_state_color)
      g.draw_text(screen_width - 16, self.margin_top + (32 / 2),
                  text=self.card.elapsed_time_string(),
                  align=Align.MiddleRight,
                  color=marked_state_color * 0.7,
                  font=self.card_status_font)
      score_fail = self.card.get_next_history_score(False)
      score = self.card.get_history_score()
      score_pass = self.card.get_next_history_score(True)
      g.draw_text(screen_center_x, self.margin_top + (32 / 2),
                  text="{:.4f} -- {:.4f} -- {:.4f}".format(score_fail, score, score_pass),
                  align=Align.Centered,
                  color=marked_state_color * 0.7,
                  font=self.card_status_font)
        
    # Draw word type
    word_type_name = self.card.word_type.name
    g.draw_text(screen_center_x, self.margin_top + 32 + 16,
                text=word_type_name,
                font=self.word_type_font,
                color=cmg.color.GRAY,
                align=Align.TopCenter)

    # Draw card text and attributes
    g.draw_text(screen_center_x, screen_center_y - 50,
                text=self.card.text[self.shown_side],
                font=self.card_font,
                color=Config.card_front_text_color,
                align=Align.Centered)
    self.draw_attributes(g, y=screen_center_y - 50 - 60,
                         attributes=self.card.attributes[self.shown_side])
    if self.revealed:
      g.draw_text(screen_center_x, screen_center_y + 50,
                  text=self.card.text[self.hidden_side],
                  font=self.card_font,
                  color=Config.card_back_text_color,
                  align=Align.Centered)
      self.draw_attributes(g, y=screen_center_y + 50 + 60,
                           attributes=self.card.attributes[self.hidden_side])

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
