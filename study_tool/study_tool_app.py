import json
import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "420,80"  # Set initial window position
import pygame
import time
import shutil
import cmg
from cmg import color
import cmg.logging
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_tool.card_set import *
from study_tool.config import Config
from study_tool.states.menu_state import MenuState
from study_tool.states.study_state import StudyState
from study_tool.states.card_list_state import CardListState
from study_tool.states.gui_state import GUIState
from study_tool.gui.card_edit_widget import CardEditWidget
from study_tool.gui.card_set_edit_widget import CardSetEditWidget
from study_tool.card_database import CardDatabase
from study_tool.scheduler import ScheduleMode
from study_tool.states.keyboard_state import KeyboardState
from study_tool.russian import conjugation
from study_tool.word_database import WordDatabase
from study_tool.example_database import ExampleDatabase
from study_tool.states.read_text_state import ReadTextState
from study_tool.states.card_edit_state import CardEditState
import yaml

DEAD_ZONE = 0.01


class StudyCardsApp(Application):

    def __init__(self):
        self.title = "Russian"
        Application.__init__(self, title=self.title, width=1100, height=900)

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

        # Filenames
        self.root_path = "data"
        self.card_data_file_name = "card_data.yaml"
        self.save_file_name = "study_data.json"
        self.word_data_file_name = "word_data.json"
        self.example_data_file_name = "examples.json"

        # Load word data
        self.word_database = WordDatabase()
        self.load_word_database()

        # Load card data
        self.card_database = CardDatabase(word_database=self.word_database)
        self.load_card_data()

        # Load card sets
        Config.logger.info("Loading card sets from: " + self.root_path)
        self.root = self.card_database.load_card_package_directory(
            path=self.root_path, name="words")
        self.save_word_database()

        # Load example data
        self.example_database = ExampleDatabase()
        self.load_example_database()
        # self.save_example_database()

        # Load study data
        self.load_study_data()

        self.save_card_data()

        self.states = []
        self.main_menu = MenuState(package=self.root)
        self.push_state(self.main_menu)
        #self.push_study_state(self.root.card_sets[1], CardSide.Russian)
        #self.push_study_state(self.root["verbs"]["nonsuffixed_stems"].card_sets[1], CardSide.English)
        #self.push_study_state(self.root["verbs"]["suffixed_stems"]["verbs_stem_ai"], CardSide.English)
        #self.push_study_state(self.root["verbs"]["suffixed_stems"]["verbs_stem_a"], CardSide.English)
        #self.push_study_state(self.root["google"]["google_doc_verbs"], CardSide.English)
        #self.push_study_state(self.root["nouns"]["nouns_arts"], CardSide.English)
        #self.push_study_state(self.root["adjectives"]["adjectives_colors"], CardSide.English)
        #self.push_study_state(self.root["new"]["new_11"], CardSide.English)
        # self.root["verbs"]["stems"].get_problem_cards()
        # self.push_card_list_state(self.root.card_sets[1])
        # self.push_state(KeyboardState())
        # self.push_state(CardEditState(card_database=self.card_database))
        cards = list(self.card_database.iter_cards())
        #self.push_state(GUIState(widget=CardEditWidget(cards[0]), title="Edit Card"))
        #self.push_state(GUIState(widget=CardSetEditWidget(self.root["verbs"]["verbs_stem_ai"], self), title="Edit Card Set"))
        self.push_state(GUIState(widget=CardSetEditWidget(self.root["nouns"]["house"], self), title="Edit Card Set"))
        #self.push_state(GUIState(widget=CardSetEditWidget(self.root["test_set"], self), title="Edit Card Set"))

        #self.save_card_set(self.root["nouns"]["house"])

        self.input.bind(pygame.K_ESCAPE, pressed=self.pop_state)

        self.input.key_pressed.connect(self.__on_key_press)
        self.input.key_released.connect(self.__on_key_release)

        Config.logger.info("Initialization complete!")

    def assimilate_card_set_to_yaml(self, card_set):
        """
        Convert a old-style text based card set file into YAML,
        moving all its cards into the global card database.
        """
        assert card_set.is_fixed_card_set()
        for card in card_set.get_cards():
            if card.get_fixed_card_set() != card_set:
                raise Exception(card_set, card)
        old_file_path = card_set.get_file_path()
        card_sets_in_file = self.card_database.get_card_sets_from_path(old_file_path)
        for file_card_set in card_sets_in_file:
            assert file_card_set.is_fixed_card_set()
            for card in file_card_set.get_cards():
                if card.get_fixed_card_set() != file_card_set:
                    raise Exception(file_card_set, card)
        assert card_set in card_sets_in_file

        # Save cards from card set into card data YAML
        card_count = 0
        for file_card_set in card_sets_in_file:
            Config.logger.info("Assimilating {} cards from card set '{}'"
                              .format(file_card_set.get_card_count(),
                                      file_card_set.get_name()))
            card_count += file_card_set.get_card_count()
            card_set.set_fixed_card_set(False)
        Config.logger.info("Saving new card data")
        self.save_card_data()

        # Replace card set text file with YAML
        for file_card_set in card_sets_in_file:
            new_path = os.path.join(os.path.dirname(old_file_path),
                                    file_card_set.key + ".yaml")
            Config.logger.info("Saving card set '{}' to: {}"
                               .format(file_card_set.get_name(), new_path))
            self.save_card_set(card_set=file_card_set, path=new_path)
        
        # Delete the old card set text file
        Config.logger.info("Removing old file: {}".format(old_file_path))
        os.remove(old_file_path)
        Config.logger.info(
            "Assimilated {} cards from {} card sets!".format(
            card_count, len(card_sets_in_file)))

    def save_card_set(self, card_set: CardSet, path=None):
        """
        Save a single card set file to YAML.
        """
        if path is None:
            path = card_set.get_file_path()
            assert path is not None
        state = card_set.serialize()
        cards_state = state["card_set"]["cards"]
        del state["card_set"]["cards"]

        with open(path, "wb") as opened_file:
            yaml.dump(state, opened_file, encoding="utf8",
                        allow_unicode=True, default_flow_style=False)
            opened_file.write(b"  cards:\n")
            for card_state in cards_state:
                opened_file.write(b"    - ")
                yaml.dump(
                    card_state, opened_file, encoding="utf8",
                    allow_unicode=True, default_flow_style=True)

    def pop_state(self):
        if len(self.states) == 1:
            self.quit()
        else:
            del self.states[-1]

    def push_state(self, state):
        state.app = self
        self.states.append(state)
        state.begin()

    def push_study_state(self, card_set, params):
        self.push_state(StudyState(card_set=card_set, params=params))

    def push_card_list_state(self, card_set):
        self.push_state(CardListState(card_set))

    def push_card_set_edit_state(self, card_set: CardSet):
        self.push_state(GUIState(widget=CardSetEditWidget(card_set, self),
                                 title="Edit Card Set"))

    def push_card_edit_state(self, card: Card):
        widget = CardEditWidget(card)
        state = GUIState(widget=widget, title="Edit Card")
        self.push_state(state)
        return widget

    def get_card_word_details(self, card):
        updated = self.word_database.populate_card_details(card, download=True)
        if updated:
            self.save_word_database()
        return card.word

    def draw_completion_bar(self, g, center_y, left, right, card_set):
        cards = []
        if isinstance(card_set, list):
            cards = card_set
        else:
            cards = list(card_set.cards)
        total_cards = len(cards)

        font = self.font_bar_text
        left_margin = g.measure_text("100%", font=font)[0] + 4
        right_margin = g.measure_text(str(9999), font=font)[0] + 4
        bar_height = g.measure_text("1", font=font)[1]
        bar_width = right - left - left_margin - right_margin
        top = center_y - (bar_height / 2)

        if False:
            cards = sorted(
                cards, key=lambda x: x.get_history_score(), reverse=True)
            for index, card in enumerate(cards):
                score = card.get_history_score()
                x = left + left_margin + bar_width * \
                    (float(index) / len(cards))
                w = max(1, math.ceil(float(bar_width) / len(cards)))
                c = math.lerp(color.RED, color.GREEN, score)
                h = math.ceil(score * bar_height)
                g.fill_rect(x, top + bar_height - h, w, h, color=c)
        else:
            x = left + left_margin
            score = 0
            for level in range(Config.proficiency_levels, -1, -1):
                count = len([c for c in cards if c.proficiency_level == level])
                if count > 0:
                    score += count * max(0, level - 1)
                    level_width = int(
                        round(bar_width * (float(count) / total_cards)))
                    if x + level_width > left + left_margin + bar_width:
                        level_width = (left + left_margin + bar_width) - x
                    g.fill_rect(x, top, level_width, bar_height,
                                color=Config.proficiency_level_colors[level])
                    x += level_width
            score /= max(1.0, float((Config.proficiency_levels - 1) * len(cards)))
            score = int(round(score * 100))
        score = 0
        g.draw_text(left + left_margin - 4, center_y, text="{}%".format(score),
                    color=color.BLACK, align=Align.MiddleRight, font=font)
        g.draw_text(right - right_margin + 4, center_y, text=str(total_cards),
                    color=color.BLACK, align=Align.MiddleLeft, font=font)

    def draw_text_box(self, text, x, y, width, height,
                      border_color=color.BLACK, border_width=2,
                      background_color=color.WHITE, text_color=color.BLACK):
        r = pygame.Rect(x, y, 0, 0)
        r.inflate_ip(width, height)
        self.graphics.fill_rect(
            r.x, r.y, r.width, r.height, color=background_color)
        self.graphics.draw_rect(
            r.x, r.y, r.width, r.height, thickness=2, color=border_color)
        self.graphics.draw_text(
            x, y, text, align=Align.Centered, color=text_color)

    @property
    def state(self):
        return self.states[-1]

    def save_card_data(self):
        path = os.path.join(self.root_path, self.card_data_file_name)
        Config.logger.info("Saving card data to: " + path)

        # Serialize the card data
        state = self.card_database.serialize_card_data()

        # Verify the serialized data can be deserialized
        #self.card_database.deserialize_card_data({"cards": state})

        # Save to temp file first
        temp_path = path + ".temp"
        with open(temp_path, "wb") as f:
            f.write(b"cards:\n")
            for card in state:
                f.write(b"- ")
                yaml.dump(card, f, encoding="utf8",
                          allow_unicode=True, default_flow_style=True)
        shutil.move(temp_path, path)

    def load_card_data(self):
        path = os.path.join(self.root_path, self.card_data_file_name)
        Config.logger.debug("Loading card data from: " + path)
        with open(path, "r", encoding="utf8") as f:
            state = yaml.safe_load(f)
            self.card_database.deserialize_card_data(state)

    def save_study_data(self):
        path = os.path.join(self.root_path, self.save_file_name)
        Config.logger.debug("Saving study data to: " + path)
        state = self.card_database.serialize_study_data()
        self.card_database.deserialize_study_data(state)
        temp_path = path + ".temp"
        with open(temp_path, "w", encoding="utf8") as f:
            json.dump(state, f, indent=2, sort_keys=True, ensure_ascii=False)
        shutil.move(temp_path, path)

    def load_study_data(self):
        path = os.path.join(self.root_path, self.save_file_name)
        if os.path.isfile(path):
            Config.logger.info("Loading study data from: " + path)
            with open(path, "r", encoding="utf8") as f:
                state = json.load(f)
                self.card_database.deserialize_study_data(state)

    def save_word_database(self):
        path = os.path.join(self.root_path, self.word_data_file_name)
        Config.logger.debug("Saving word data to: " + path)
        self.word_database.save(path)

    def load_word_database(self):
        path = os.path.join(self.root_path, self.word_data_file_name)
        if os.path.isfile(path):
            Config.logger.info("Loading word data from: " + path)
            self.word_database.load(path)

    def save_example_database(self):
        path = os.path.join(self.root_path, self.example_data_file_name)
        Config.logger.debug("Saving example data to: " + path)
        self.example_database.save(path)

    def load_example_database(self):
        #path = os.path.join(self.root_path, self.example_data_file_name)
        # if os.path.isfile(path):
        #  Config.logger.info("Loading example data from: " + path)
        #  self.example_database.load(path)
        for story_filename in os.listdir(self.root_path + "/examples/stories"):
            Config.logger.info("Loading example story " + story_filename)
            story_path = self.root_path + "/examples/stories/" + story_filename
            self.example_database.load_story_text_file(story_path)

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

    def __on_key_press(self, key, text):
        self.state.on_key_press(key, text)

    def __on_key_release(self, key):
        self.state.on_key_release(key)


if __name__ == "__main__":
    app = StudyCardsApp()
    app.run()
