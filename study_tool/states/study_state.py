from enum import IntEnum
import os
import pygame
import random
import threading
import time
import win32clipboard
import cmg
from cmg import math
from cmg.math import Vec2
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from study_tool import card_attributes
from study_tool.card import Card, CardSide
from study_tool.card_attributes import *
from study_tool.card_set import CardSet, CardSetPackage, StudySet
from study_tool.config import Config
from study_tool.russian.types import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.scheduler import Scheduler
from study_tool.scheduler import SchedulerParams
from study_tool.states.state import State, Button
from study_tool.states.sub_menu_state import SubMenuState
from study_tool import example_database
from study_tool.entities.word_box import WordBox
from study_tool.entities.conjugation_table import ConjugationTable
from study_tool.entities.text_label import TextLabel
from study_tool.entities.entity import Entity
from study_tool.entities.label_box import LabelBox
from study_tool.entities.card_attribute_box import CardAttributeBox
from study_tool.entities.study_proficiency_bar import StudyProficiencyBar
from study_tool.gui.related_cards_widget import RelatedCardsWidget
from study_tool.gui.add_card_to_set_widget import AddCardToSetWidget
from study_tool.states.gui_state import GUIState


class StudyParams:
    def __init__(self,
                 random_side=True,
                 random_form=False,
                 shown_side=CardSide.English):
        self.random_side = random_side
        self.random_form = random_form
        self.shown_side = shown_side


class ExampleThread(threading.Thread):
    """
    Thread to find example sentences from the example database for each card.
    """
    def __init__(self, example_database, cards: list):
        threading.Thread.__init__(self)
        self.__example_database = example_database
        self.__cards = list(cards)
        self.__running = False
        self.__lock = threading.Lock()
        self.__card_example_dict = {}

    def get_examples(self, card) -> list:
        with self.__lock:
            if card in self.__card_example_dict:
                return self.__card_example_dict[card]
        examples = self.find_examples(card)
        with self.__lock:
            self.__card_example_dict[card] = examples
            return self.__card_example_dict[card]

    def stop(self):
        self.__running = False
        self.join()

    def run(self):
        self.__running = True
        for card in self.__cards:
            time.sleep(0.05)
            examples = self.find_examples(card)
            with self.__lock:
                self.__card_example_dict[card] = examples
            if not self.__running:
                break
        self.__running = False

    def find_examples(self, card: Card) -> list:
        word_patterns = self.__example_database.get_word_patterns(
            card.get_russian().text)
        auto_examples = list(self.__example_database.iter_example_sentences_2(
            word_patterns))
        random.shuffle(auto_examples)
        import time
        return auto_examples


class StudyState(State):
    def __init__(self,
                 card_set: StudySet,
                 study_params=StudyParams(),
                 scheduler_params: SchedulerParams=None):
        super().__init__()

        # Formatting
        self.card_status_font = cmg.Font(30)
        self.__left_margin = 20
        self.__bottom_margin = 10
        self.__card_text_area_height = 80
        self.proficiency_margin_height = 32
        self.__line_spacing = 22
        self.__card_box_spacing = 4
        self.__table_row_height = 22
        self.__font_details = cmg.Font(24)
        self.__font_card_attributes = cmg.Font(30)
        self.__font_word_type = cmg.Font(34)

        # Study settings
        self.card_set = card_set
        self.shown_side = CardSide.English
        self.params = study_params
        self.__scheduler_params = scheduler_params

        # Entities
        self.__entity_reveal_root = None
        self.__entity_word_type_label = None
        self.__entity_verb_root = None
        self.__entity_noun_root = None
        self.__entity_example_root = None
        self.__entity_adjective_root = None
        self.__entity_related_cards = None
        self.__entity_counterparts = None
        self.__entity_prompt_text = None
        self.__entity_reveal_text = None
        self.__entity_prompt_attributes = None
        self.__entity_reveal_attributes = None
        self.__entity_word_translation = None
        self.__entity_word_details = None
        self.__table_noun = None
        self.__table_adjective = None
        self.__table_verb_past = None
        self.__table_verb_present = None
        self.__table_verb_participles = None
        self.__table_card_sets = None
        self.__proficiency_bar = None

        # Internal state
        self.card = None
        self.__wiktionary_term = None
        self.__sound = None
        self.__example_thread = None
        self.__study_data = None
        self.__study_metrics = None
        self.revealed = False
        self.reveal_text = AccentedText()
        self.prompt_text = AccentedText()
        self.prompt_attributes = []
        self.reveal_attributes = []
        self.scheduler = None

    def begin(self):
        """Begin the state."""
        self.buttons[0] = Button("Reveal", self.reveal)
        self.buttons[1] = Button("Exit", self.pause)
        self.buttons[2] = Button("Next", lambda: self.next(knew_it=True))
        
        self.__example_thread = ExampleThread(
            example_database=self.app.example_database,
            cards=self.card_set.get_cards())
        self.__example_thread.start()

        self.scheduler = Scheduler(cards=self.card_set.cards,
                                   study_database=self.app.study_database,
                                   params=self.__scheduler_params)
        self.seen_cards = []
        self.card = None
        self.__study_data = None
        self.revealed = False
        self.__related_cards = []
        self.__counterparts = []

        self.__entity_reveal_root = self.add_entity(Entity())
        self.__entity_noun_root = self.__entity_reveal_root.add_child(Entity())
        self.__entity_adjective_root = self.__entity_reveal_root.add_child(Entity())
        self.__entity_verb_root = self.__entity_reveal_root.add_child(Entity())
        self.__entity_example_root = self.__entity_reveal_root.add_child(Entity())
        self.__entity_prompt_attributes = self.add_entity(Entity())
        self.__entity_reveal_attributes = self.__entity_reveal_root.add_child(Entity())

        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        
        self.__proficiency_bar = StudyProficiencyBar(
            center_y=self.margin_top / 2,
            left=screen_center_x + 80,
            right=screen_width - 32,
            study_set=self.card_set)
        self.add_entity(self.__proficiency_bar)

        self.__entity_prompt_text = self.add_entity(LabelBox(
            text="<PROMPT-TEXT>",
            font=None,
            color=Colors.BLACK,
            align=Align.Centered,
            max_font_size=74,
            min_font_size=12))
        self.__entity_reveal_text = self.__entity_reveal_root.add_child(LabelBox(
            text="<REVEAL-TEXT>",
            font=None,
            color=Colors.BLACK,
            align=Align.Centered,
            max_font_size=74,
            min_font_size=16))
        h = self.__card_text_area_height
        self.__entity_prompt_text.set_rect(0, screen_center_y - h, screen_width, h)
        self.__entity_reveal_text.set_rect(0, screen_center_y, screen_width, h)
        
        # Draw word type at top-middle
        self.__entity_word_type_label = self.add_entity(
            TextLabel(
                text="<WORD-TYPE>",
                font=self.__font_word_type,
                color=Colors.GRAY,
                align=Align.TopCenter),
            pos=Vec2(screen_center_x, self.margin_top + 32 + 16))
        
        # Card Set list
        card_sets = []
        for card_set in Config.app.card_database.iter_card_sets():
            if card_set.has_card(self.card):
                card_sets.append(card_set)
        x = screen_width - 16 - 400
        y = screen_height - self.margin_bottom - 16 - self.__line_spacing
        self.__table_card_sets = ConjugationTable(
            font=self.__font_details,
            row_count=1,
            column_header_count=0,
            column_count=1,
            column_widths=[400],
            row_height=self.__table_row_height)
        self.__table_card_sets.set_text(0, 0, "Found in Card Sets")
        self.__entity_reveal_root.add_child(self.__table_card_sets, pos=Vec2(x, y))

        y = screen_height - self.margin_bottom - 20 - (22 * 8) - 12 - (25 * 2)
        self.__entity_related_cards = self.__entity_reveal_root.add_child(
            TextLabel("Related cards:", font=self.__font_details),
            pos=Vec2(self.__left_margin, y))
        y += self.__line_spacing
        self.__entity_counterparts = self.__entity_verb_root.add_child(
            TextLabel("Imperfective Counterparts:", font=self.__font_details),
            pos=Vec2(self.__left_margin, y))
        y += self.__line_spacing
        self.__entity_word_translation = self.__entity_verb_root.add_child(
            TextLabel("<translation>", font=self.__font_details),
            pos=Vec2(self.__left_margin, y))
        y += self.__line_spacing
        self.__entity_word_details = self.__entity_verb_root.add_child(
            TextLabel("<details>", font=self.__font_details),
            pos=Vec2(self.__left_margin, y))

        table_bottom = screen_height - self.margin_bottom - self.__bottom_margin

        # Create the Verb Non-Past Tense conjugation table
        table_x = self.__left_margin
        self.__table_verb_present = ConjugationTable(
            font=self.__font_details,
            row_count=7,
            column_count=2,
            column_widths=(40, 160),
            row_height=self.__table_row_height)
        self.__table_verb_present.set_text(0, 1, "Present Tense")
        self.__table_verb_present.set_text(1, 0, "я")
        self.__table_verb_present.set_text(2, 0, "ты")
        self.__table_verb_present.set_text(3, 0, "он")
        self.__table_verb_present.set_text(4, 0, "мы")
        self.__table_verb_present.set_text(5, 0, "вы")
        self.__table_verb_present.set_text(6, 0, "они")
        self.__entity_verb_root.add_child(
            self.__table_verb_present,
            pos=Vec2(table_x, table_bottom - (self.__table_row_height * 7)))
        table_x += self.__table_verb_present.get_width() + 16

        # Create the Verb Past Tense conjugation table
        self.__table_verb_past = ConjugationTable(
            font=self.__font_details,
            row_count=7,
            column_count=2,
            column_widths=(50, 160),
            row_height=self.__table_row_height)
        self.__table_verb_past.set_text(0, 1, "Past Tense")
        self.__table_verb_past.set_text(1, 0, "он")
        self.__table_verb_past.set_text(2, 0, "она")
        self.__table_verb_past.set_text(3, 0, "оно")
        self.__table_verb_past.set_text(4, 0, "они")
        self.__table_verb_past.set_text(5, 0, "imp1")
        self.__table_verb_past.set_text(6, 0, "imp2")
        self.__entity_verb_root.add_child(
            self.__table_verb_past,
            pos=Vec2(table_x, table_bottom - (self.__table_row_height * 7)))
        table_x += self.__table_verb_past.get_width() + 16
        
        # Create the Verb Participle conjugation table
        self.__table_verb_participles = ConjugationTable(
            font=self.__font_details,
            row_count=4,
            column_count=3,
            column_widths=(100, 160, 160),
            row_height=self.__table_row_height)
        self.__table_verb_participles.set_text(0, 1, "Present")
        self.__table_verb_participles.set_text(0, 2, "Past")
        self.__table_verb_participles.set_text(1, 0, "Active")
        self.__table_verb_participles.set_text(2, 0, "Adverbial")
        self.__table_verb_participles.set_text(3, 0, "Passive")
        self.__entity_verb_root.add_child(
            self.__table_verb_participles,
            pos=Vec2(table_x, table_bottom - (self.__table_row_height * 4)))
        
        # Create the Adjective conjugation table
        self.__table_adjective = ConjugationTable(
            font=self.__font_details,
            row_count=8,
            column_count=5,
            column_widths=(120, 180, 180, 180, 180),
            row_height=self.__table_row_height)
        self.__table_adjective.set_text(0, 0, "Case")
        self.__table_adjective.set_text(0, 1, "Masculine")
        self.__table_adjective.set_text(0, 2, "Neuter")
        self.__table_adjective.set_text(0, 3, "Femanine")
        self.__table_adjective.set_text(0, 4, "Plural")
        self.__table_adjective.set_text(7, 0, "Short")
        for index, case in enumerate(Case):
            self.__table_adjective.set_text(1 + index, 0, case.name)
        self.__entity_adjective_root.add_child(
            self.__table_adjective,
            pos=Vec2(self.__left_margin, table_bottom - (self.__table_row_height * 8)))
        
        # Create the Noun conjugation table
        self.__table_noun = ConjugationTable(
            font=self.__font_details,
            row_count=7,
            column_count=3,
            column_widths=(120, 180, 180),
            row_height=self.__table_row_height)
        self.__table_noun.set_text(0, 0, "Case")
        self.__table_noun.set_text(0, 1, "Singular")
        self.__table_noun.set_text(0, 2, "Plural")
        for index, case in enumerate(Case):
            self.__table_noun.set_text(1 + index, 0, case.name)
        self.__entity_noun_root.add_child(
            self.__table_noun,
            pos=Vec2(self.__left_margin, table_bottom - (self.__table_row_height * 7)))
        
        self.__tables = [self.__table_noun,
                         self.__table_adjective,
                         self.__table_verb_present,
                         self.__table_verb_past,
                         self.__table_verb_participles]

        self.next_card()

    def on_end(self):
        """Called when the state ends."""
        self.__example_thread.stop()
        
    def on_key_pressed(self, key, mod, text):
        """Called when a key is pressed."""
        if KeyMods.LSHIFT not in mod and KeyMods.LCTRL not in mod:

            # R: Edit related cards
            if key == Keys.K_R:
                self.__on_click_edit_related_cards()

            # S: Add card to set
            if key == Keys.K_S:
                self.__on_click_add_to_set()

            # E: Edit related cards
            elif key == Keys.K_E:
                self.__on_click_edit_card()

        elif KeyMods.LCTRL in mod and KeyMods.LSHIFT not in mod:
            # Ctrl+C: Copy Russian text
            if key == Keys.K_C:
                text = self.card.get_russian().text
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                finally:
                    win32clipboard.CloseClipboard()

    def pause(self):
        other_side = CardSide(1 - self.shown_side)
        options =  [("Resume", None),
                    ("Edit Card", self.__on_click_edit_card),
                    ("Edit Related Cards", self.__on_click_edit_related_cards)]
        if isinstance(self.card_set, CardSet):
            options.append(("Edit Set", self.__on_click_edit_card_set))
        options += [
             ("List", lambda: (self.app.pop_state(),
                               self.app.push_card_list_state(self.card_set))),
             ("Menu", self.app.pop_state),
             ("Exit", self.app.quit)]
        self.app.push_state(SubMenuState("Pause", options))
    
    def __on_click_edit_card(self):
        """Called to begin editing the current card."""
        widget = self.app.push_card_edit_state(
            self.card, allow_card_change=False)
        widget.updated.connect(self.__on_card_updated)
    
    def __on_click_edit_related_cards(self):
        """Called to begin editing the current card's related cards."""
        widget = RelatedCardsWidget(self.card, self.app)
        widget.updated.connect(self.__on_card_updated)
        self.app.push_gui_state(widget)
    
    def __on_click_add_to_set(self):
        """Called to begin editing the current card's related cards."""
        widget = AddCardToSetWidget(self.card, self.app)
        widget.updated.connect(self.__on_card_updated)
        self.app.push_gui_state(widget)
    
    def __on_click_edit_card_set(self):
        """Called to begin editing the card set."""
        self.app.pop_state()
        widget = self.app.push_card_set_edit_state(self.card_set)

    def __on_card_updated(self, card: Card):
        """Called after a card is edited."""
        self.show_card(card)

    def __on_revealed_changed(self):
        """Called revealed or un-revealed."""
        self.__entity_reveal_root.set_visible(self.revealed)
        self.__entity_noun_root.set_visible(isinstance(self.card.word, Noun))
        self.__entity_adjective_root.set_visible(isinstance(self.card.word, Adjective))
        self.__entity_verb_root.set_visible(isinstance(self.card.word, Verb))
        
    def next(self, knew_it=True):
        """
        Mark the current card as "knew it" or "did NOT know it"
        then move to the next card.
        """
        self.scheduler.mark(self.card, knew_it=knew_it)

        self.next_card()

        # Save study data in the background
        import threading
        thread = threading.Thread(target=self.app.save_study_data)
        thread.start()

    def __get_random_russian_form(self, card: Card, word: Word):
        """Get a random form of a russian word."""
        if isinstance(word, Verb):
            odds = random.randint(1, 10)
            if odds <= 3:
                plurality = random.choice([pl for pl in Plurality])
                person = random.choice([p for p in Person])
                conjugation = word.get_non_past(
                    plurality=plurality, person=person)
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
        """Chooses the next card and shows it."""
        card = self.scheduler.next()
        if card is None:
            self.app.pop_state()
            Config.logger.info("No cards left to study!")
        else:
            self.show_card(card)
        
    def show_card(self, card: Card):
        """Shows a new card."""

        self.card = card
        self.__study_data = Config.app.study_database.get_card_study_data(card)
        self.__proficiency_bar.recalculate()
        self.__study_metrics = Config.app.study_database.get_group_study_metrics(self.card_set)
        self.revealed = False
        self.buttons[0] = Button("Reveal", self.reveal)

        # Pick the side to show
        if self.params.random_side:
            self.shown_side = random.choice(
                [CardSide.English, CardSide.Russian])
        else:
            self.shown_side = self.params.shown_side
        reveal_side = 1 - self.shown_side

        # Get word info associated with this card
        word = self.app.word_database.get_word(
            name=self.card.word_name,
            word_type=self.card.get_word_type())
        if word is not None:
            forms = word.get_all_forms()
        else:
            forms = self.card.get_russian().text
        self.__wiktionary_term = None
        self.__sound = None
        term_name = self.card.get_russian()
        if word:
            term_name = word.get_name()
        self.__wiktionary_term = Config.app.wiktionary.get_term(term_name)
        self.__sound = Config.app.wiktionary.get_sound(term_name)
        if not self.__sound:
            Config.app.wiktionary.download_sound(term_name)
            self.__sound = Config.app.wiktionary.get_sound(term_name)
        if self.__sound:
            self.__sound.play()
        print(term_name, self.__wiktionary_term, self.__sound)

        # Get the card text and attributes
        self.prompt_attributes = []
        if (self.params.random_form and self.shown_side == CardSide.Russian and
                word is not None):
            # Get a random form of the card's word
            self.prompt_text, self.reveal_attributes = (
                self.__get_random_russian_form(card=self.card, word=word))
            self.reveal_attributes += self.card.get_attributes()
            self.reveal_text = self.card.get_text(CardSide.English)
        else:
            self.prompt_text = self.card.get_text(self.shown_side)
            self.reveal_text = self.card.get_text(reveal_side)
            self.reveal_attributes = self.card.get_attributes()
            if self.shown_side == CardSide.English:
                self.prompt_attributes = [a for a in self.card.get_attributes()
                                          if a in ENGLISH_SIDE_CARD_ATTRIBUTES]

        # Get examples and word occurences in the example
        self.__entity_example_root.destroy_children()
        max_examples = Config.max_examples_to_display
        examples = []
        for example in self.card.get_examples():
            examples.append((example, example_database.get_word_occurances(
                word=forms, text=example.text)))
        total_example_count = len(examples)
        if len(examples) < max_examples:
            auto_examples = self.__example_thread.get_examples(self.card)
            examples += auto_examples[:max_examples - len(examples)]
            total_example_count += len(auto_examples)
        y = self.margin_top + self.proficiency_margin_height + 60
        for index, (sentence, occurences) in enumerate(examples):
            self.__entity_example_root.add_child(
                TextLabel(text=AccentedText(sentence).text,
                          font=self.__font_details,
                          color=Colors.BLACK,
                          align=Align.TopLeft),
                pos=Vec2(self.__left_margin, y))
            if occurences is None:
                occurences = []
            for start, word in occurences:
                size = self.__font_details.measure(sentence[:start - 1])
                self.__entity_example_root.add_child(
                    TextLabel(text=word,
                              font=self.__font_details,
                              color=Colors.RED,
                              align=Align.TopLeft),
                    pos=Vec2(self.__left_margin + size.x, y))
            y += self.__line_spacing
        if examples:
            self.__entity_example_root.add_child(
                TextLabel(text="({} total examples)".format(total_example_count),
                          font=self.__font_details,
                          color=Colors.GRAY,
                          align=Align.TopLeft),
                pos=Vec2(self.__left_margin, y))

        self.__entity_prompt_text.set_text(self.prompt_text)
        self.__entity_reveal_text.set_text(self.reveal_text)
        self.__entity_word_type_label.set_text(self.card.get_word_type().name)

        # Create card attribute labels
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        attr_spacing = 16
        y1 = self.__entity_prompt_text.get_rect().top
        y2 = self.__entity_reveal_text.get_rect().bottom
        for parent, attributes, y, top in (
            (self.__entity_prompt_attributes, self.prompt_attributes, y1, True),
            (self.__entity_reveal_attributes, self.reveal_attributes, y2, False)):
            # Measure the width of each attribute text
            attributes = sorted(attributes, key=lambda x: x.name)
            parent.destroy_children()
            boxes = []
            total_attr_width = 0
            for index, attr in enumerate(attributes):
                box = CardAttributeBox(attribute=attr, short=False, font=self.__font_card_attributes)
                boxes.append(box)
                parent.add_child(box)
                total_attr_width += box.get_width()
                if index > 0:
                    total_attr_width += attr_spacing

            # Set position for each attribute box
            x = screen_center_x - (total_attr_width / 2)
            for box in boxes:
                box.set_x(x)
                if top:
                    box.set_y(y - box.get_height())
                else:
                    box.set_y(y)
                x += box.get_width() + attr_spacing
                
        # Card Set list
        card_sets = []
        for card_set in Config.app.card_database.iter_card_sets():
            if card_set.has_card(self.card):
                card_sets.append(card_set)
        self.__table_card_sets.set_row_count(1 + len(card_sets))
        for index, card_set in enumerate(card_sets):
            self.__table_card_sets.set_text(index + 1, 0, card_set.get_name())
        self.__table_card_sets.set_y(
            screen_height - self.margin_bottom - 16 -
            self.__table_card_sets.get_height())

        # Reset conjugation tables
        for table in self.__tables:
            if self.shown_side == CardSide.Russian:
                table.set_highlighted_text(self.prompt_text)
            else:
                table.set_highlighted_text(self.reveal_text)

        for entity in self.__counterparts:
            entity.destroy()
        self.__counterparts = []
        for entity in self.__related_cards:
            entity.destroy()
        self.__related_cards = []

        # Create list of related cards
        self.__entity_related_cards.set_text("Related cards:")
        x = (self.__entity_related_cards.get_position().x +
             self.__entity_related_cards.get_width() + self.__card_box_spacing)
        y = self.__entity_related_cards.get_position().y
        for related_card in self.card.get_related_cards():
            entity = self.__entity_related_cards.add_child(
                WordBox(related_card, font=self.__font_details), pos=Vec2(x, y))
            self.__related_cards.append(entity)
            x += entity.get_width() + self.__card_box_spacing
            
        # Populate Noun conjugation tables
        if self.card.word is not None and isinstance(self.card.word, Noun):
            noun = self.card.word
            for index, case in enumerate(Case):
                self.__table_noun.set_text(1 + index, 1, noun.get_declension(
                    case=case, plurality=Plurality.Singular))
                self.__table_noun.set_text(1 + index, 2, noun.get_declension(
                    case=case, plurality=Plurality.Plural))

        # Populate Adjective conjugation tables
        elif self.card.word is not None and isinstance(self.card.word, Adjective):
            adj = self.card.word
            for index, case in enumerate(Case):
                self.__table_adjective.set_text(1 + index, 1, adj.get_declension(
                    case=case, gender=Gender.Masculine))
                self.__table_adjective.set_text(1 + index, 2, adj.get_declension(
                    case=case, gender=Gender.Neuter))
                self.__table_adjective.set_text(1 + index, 3, adj.get_declension(
                    case=case, gender=Gender.Femanine))
                self.__table_adjective.set_text(1 + index, 4, adj.get_declension(
                    case=case, plurality=Plurality.Plural))
            self.__table_adjective.set_text(7, 1, adj.get_declension(
                short=True, gender=Gender.Masculine))
            self.__table_adjective.set_text(7, 2, adj.get_declension(
                short=True, gender=Gender.Neuter))
            self.__table_adjective.set_text(7, 3, adj.get_declension(
                short=True, gender=Gender.Femanine))
            self.__table_adjective.set_text(7, 4, adj.get_declension(
                short=True, plurality=Plurality.Plural))
            
        # Populate Verb conjugation tables
        elif self.card.word is not None and isinstance(self.card.word, Verb):
            verb = self.card.word
            other_aspect = Aspect(1 - verb.aspect)
            
            self.__entity_word_translation.set_text(
                verb.infinitive + " -- " + verb.translation)
            self.__entity_word_details.set_text(verb.info)

            # Create list of counterparts
            self.__entity_counterparts.set_text(other_aspect.name + " Counterparts:")
            x = (self.__entity_counterparts.get_position().x +
                 self.__entity_counterparts.get_width() +
                 self.__card_box_spacing)
            y = self.__entity_counterparts.get_position().y
            for counterpart in verb.get_counterparts():
                entity = self.__entity_counterparts.add_child(
                    WordBox(counterpart, font=self.__font_details), pos=Vec2(x, y))
                self.__counterparts.append(entity)
                x += entity.get_width() + self.__card_box_spacing

            # Present/Future tense
            title = "Present" if verb.aspect == Aspect.Imperfective else "Future"
            title += " Tense"
            self.__table_verb_present.set_text(0, 1, title)
            for index, (plurality, person) in enumerate([
                    (Plurality.Singular, Person.First),
                    (Plurality.Singular, Person.Second),
                    (Plurality.Singular, Person.Third),
                    (Plurality.Plural, Person.First),
                    (Plurality.Plural, Person.Second),
                    (Plurality.Plural, Person.Third)]):
                conjugation = verb.non_past[(plurality, person)]
                self.__table_verb_present.set_text(1 + index, 1, conjugation)

            # Past tense
            for index, (plurality, gender) in enumerate([
                    (Plurality.Singular, Gender.Masculine),
                    (Plurality.Singular, Gender.Femanine),
                    (Plurality.Singular, Gender.Neuter),
                    (Plurality.Plural, None)]):
                conjugation = verb.past[(plurality, gender)]
                self.__table_verb_past.set_text(1 + index, 1, conjugation)
            self.__table_verb_past.set_text(5, 1, verb.imperative[Plurality.Singular])
            self.__table_verb_past.set_text(6, 1, verb.imperative[Plurality.Plural])

            # Participles
            self.__table_verb_participles.set_text(1, 1, verb.get_participle(Participle.Active, Tense.Present))
            self.__table_verb_participles.set_text(1, 2, verb.get_participle(Participle.Active, Tense.Past))
            self.__table_verb_participles.set_text(2, 1, verb.get_participle(Participle.Adverbial, Tense.Present))
            self.__table_verb_participles.set_text(2, 2, verb.get_participle(Participle.Adverbial, Tense.Past))
            self.__table_verb_participles.set_text(3, 1, verb.get_participle(Participle.Passive, Tense.Present))
            self.__table_verb_participles.set_text(3, 2, verb.get_participle(Participle.Passive, Tense.Past))

        self.__on_revealed_changed()
        Config.logger.info("Showing card: " + repr(self.prompt_text))

    def reveal(self):
        """Reveal the other side of the card."""
        self.revealed = True
        self.buttons[0] = Button("Mark", lambda: self.next(knew_it=False))
        self.__on_revealed_changed()

    def draw_top_proficiency_bar(self, g: Graphics, top_y, bar_height, bar_color):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2
        marked_overlay_color = bar_color * 0.7

        # Draw recent history (left)
        max_history_display_count = 10
        history_display_count = min(max_history_display_count,
                                    len(self.__study_data.get_history_list()))
        history_box_size = 20
        padding = (self.proficiency_margin_height - history_box_size) // 2
        spacing = 3
        for index in range(0, history_display_count):
            marked = not self.__study_data.get_history_list()[index]
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
                    text=self.__study_data.elapsed_time_string(),
                    align=Align.MiddleRight,
                    color=marked_overlay_color,
                    font=self.card_status_font)

        # Draw current and predicted history score (middle)
        score_fail = self.__study_data.get_next_history_score(False)
        score = self.__study_data.get_history_score()
        score_pass = self.__study_data.get_next_history_score(True)
        g.draw_text(screen_center_x, top_y + (bar_height // 2),
                    text="{:.4f} < {:.4f} > {:.4f}".format(
                        score_fail, score, score_pass),
                    align=Align.Centered,
                    color=marked_overlay_color,
                    font=self.card_status_font)

    def draw(self, g: Graphics):
        screen_width, screen_height = self.app.screen.get_size()
        screen_center_x = screen_width / 2
        screen_center_y = screen_height / 2

        # Draw top/bottom proficiency bars
        if self.__study_data.get_proficiency_level() > 0:
            marked_state_color = cmg.math.lerp(Config.proficiency_level_colors[
                self.__study_data.get_proficiency_level()], color.WHITE, 0.7)
            g.fill_rect(0, self.margin_top, screen_width,
                        self.proficiency_margin_height,
                        color=marked_state_color)
            if not self.revealed:
                g.fill_rect(0, screen_height - self.margin_bottom - self.proficiency_margin_height,
                            screen_width, self.proficiency_margin_height,
                            color=marked_state_color)
            self.draw_top_proficiency_bar(g, self.margin_top,
                                          self.proficiency_margin_height,
                                          bar_color=marked_state_color)

        # Draw state
        State.draw(self, g)

        # Draw text at top
        g.draw_text(32, self.margin_top / 2,
                    text=self.card_set.name,
                    color=cmg.color.GRAY,
                    align=Align.MiddleLeft)
        g.draw_text(screen_center_x, self.margin_top / 2,
                    text="{:.0f} / {:.0f}".format(self.__study_metrics.get_proficiency_count(),
                                                  self.__study_metrics.history_score),
                    color=cmg.color.GRAY,
                    align=Align.Centered)
        