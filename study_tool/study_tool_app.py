import json
import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "200,80"  # Set initial window position
import pygame
import threading
import time
import shutil
import yaml
import cmg
from cmg import color
import cmg.logging
from cmg import math
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from study_tool.card_database import CardDatabase
from study_tool.card_set import *
from study_tool.card_set import StudySet
from study_tool.config import Config
from study_tool.example_database import ExampleDatabase
from study_tool.gui.card_edit_widget import CardEditWidget
from study_tool.gui.card_set_edit_widget import CardSetEditWidget
from study_tool.gui.related_cards_widget import RelatedCardsWidget
from study_tool.gui.add_card_to_set_widget import AddCardToSetWidget
from study_tool.gui.query_widget import QueryWidget
from study_tool.gui.card_set_browser_widget import CardSetBrowserWidget
from study_tool.gui.card_set_browser_widget import CardSetPackageBrowserWidget
from study_tool.gui.card_search_widget import CardSearchWidget
from study_tool.query import CardQuery
from study_tool.russian import conjugation
from study_tool.russian.word import WordSourceEnum
from study_tool.scheduler import SchedulerParams
from study_tool.states.menu_state import MenuState
from study_tool.states.study_state import StudyState
from study_tool.states.card_list_state import CardListState
from study_tool.states.gui_state import GUIState
from study_tool.states.keyboard_state import KeyboardState
from study_tool.states.read_text_state import ReadTextState
from study_tool.states.study_state import StudyParams
from study_tool.study_database import StudyDatabase
from study_tool.word_database import WordDatabase
from study_tool.external.cooljugator import CooljugatorThread

PRESS_THRESHOLD = 0.05
DEAD_ZONE = 0.002

class StudyCardsApp(Application):

    def __init__(self):
        Config.app = self
        self.title = "Russian"
        Application.__init__(self, title=self.title, width=1500, height=900)

        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.font_bar_text = pygame.font.Font(None, 30)
        self.__font_fps = cmg.Font(24)
        self.__font_status = cmg.Font(20)

        self.clock = pygame.time.Clock()
        self.graphics = Graphics(self.screen)
        self.joystick_ready = False
        self.inputs = [
            Input(index=2, name="Middle", reversed=True, max=1, min=-1),
            Input(index=1, name="Left", reversed=True, max=1, min=-1),
            Input(index=3, name="Right", reversed=True, max=1, min=-1)]

        # Filenames
        self.root_path = "data"
        self.cards_path = os.path.join(self.root_path, "cards")
        self.card_data_file_name = "card_data.yaml"
        self.save_file_name = "study_data.yaml"
        self.word_data_file_name = "word_data.json"
        self.custom_word_data_file_name = "custom_words.yaml"
        self.example_data_file_name = "examples.json"

        # Create databases
        self.word_database = WordDatabase()
        self.card_database = CardDatabase(word_database=self.word_database)
        self.example_database = ExampleDatabase(word_database=self.word_database)
        self.study_database = StudyDatabase(card_database=self.card_database)
        self.cooljugator_thread = CooljugatorThread(self.word_database.get_cooljugator())

        # Load data
        self.load_word_database()
        self.load_card_data()
        self.card_database.load_card_sets(self.cards_path)
        self.load_example_database()
        self.load_study_data()
        self.save_word_database()

        Config.logger.info("Initialization complete!")

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
        cards = list(self.card_database.iter_cards())
        test_set = self.root["test_set"]
        test_card = list(self.card_database.find_cards_by_word("слушать"))[0]
        #self.push_card_edit_state(None)
        #self.push_card_edit_state(cards[0])
        #self.push_state(GUIState(widget=CardSetEditWidget(self.root["verbs"]["verbs_stem_ai"], self), title="Edit Card Set"))
        #self.push_state(GUIState(widget=CardSetEditWidget(self.root["nouns"]["house"], self), title="Edit Card Set"))
        #self.push_gui_state(CardSetEditWidget(test_set, self))
        #self.push_gui_state(CardEditWidget(test_card, self))
        #self.push_gui_state(RelatedCardsWidget(test_card, self))
        #self.push_gui_state(AddCardToSetWidget(test_card, self))
        #self.push_card_edit_state(card, close_on_apply=False, allow_card_change=True)
        self.push_study_state(test_set, study_params=StudyParams(random_side=True))
        #self.push_study_state(test_set, study_params=StudyParams(random_side=True), scheduler_params=SchedulerParams(max_repetitions=1))
        #self.push_state(GUIState(widget=QueryWidget(self, test_set.get_cards()), title="Study Query"))
        #self.push_gui_state(CardSetBrowserWidget(self.card_database.get_root_package()))
        #self.push_gui_state(CardSetPackageBrowserWidget(self.card_database.get_root_package()))
        #self.push_gui_state(CardSearchWidget())

        self.input.bind(pygame.K_ESCAPE, pressed=self.pop_state)

        self.input.key_pressed.connect(self.__on_key_pressed)
        self.input.key_released.connect(self.__on_key_released)
        self.input.mouse_pressed.connect(self.__on_mouse_pressed)
        self.input.mouse_released.connect(self.__on_mouse_released)

        #self.get_unknown_words_from_examples()
        self.cooljugator_thread.start()

    def on_quit(self):
        self.cooljugator_thread.stop()

    def on_window_resized(self, size: Vec2):
        self.graphics = Graphics(self.screen)

    @property
    def root(self) -> CardSetPackage:
        return self.card_database.get_root_package()

    def iter_card_sets(self):
        """Iterate all card sets"""
        for card_set in self.root.all_card_sets():
            yield card_set

    def query_cards(self, query: CardQuery):
        """Iterates cards using a query."""
        count = 0
        for _, card in self.card_database.cards.items():
            study_data = self.study_database.get_card_study_data(card)
            if query.matches(card, study_data):
                yield card
                count += 1
                if query.max_count is not None and count >= query.max_count:
                    break

    def get_unknown_words_from_examples(self):
        story = self.example_database.get_story("Проблемы и сложности попытки назначить свидание Твайлайт Спаркл")
        print(story)
        frequencies = {}
        for text in story.iter_words():
            text = text.lower().replace("ё", "е")
            words = self.word_database.lookup_word(text)
            if not words:
                key = text
                frequencies[key] = frequencies.get(key, 0) + 1
            # if words:
            #     word = words[0]
            #     key = word.get_key()
            #     frequencies[key] = frequencies.get(key, 0) + 1
        result = list(frequencies.items())
        result.sort(key=lambda x: x[1], reverse=True)
        for word, count in result[:50]:
            print("{} {}".format(count, word))

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
            file_card_set.set_fixed_card_set(False)
        Config.logger.info("Saving new card data")
        self.card_database.save_card_data()

        # Replace card set text file with YAML
        for file_card_set in card_sets_in_file:
            new_path = os.path.join(os.path.dirname(old_file_path),
                                    file_card_set.key + ".yaml")
            Config.logger.info("Saving card set '{}' to: {}"
                               .format(file_card_set.get_name(), new_path))
            self.save_card_set(card_set=file_card_set, path=new_path)
        
        # Delete the old card set text file
        Config.logger.info("Removing old file: {}".format(old_file_path))
        self.card_database.remove_card_set_path(old_file_path)
        os.remove(old_file_path)
        Config.logger.info(
            "Assimilated {} cards from {} card sets!".format(
            card_count, len(card_sets_in_file)))

    def save_card_set(self, card_set: CardSet, path=None):
        """Save a single card set file to YAML."""
        self.card_database.save_card_set(card_set=card_set, path=path)

    def pop_state(self):
        if len(self.states) == 1:
            self.quit()
        else:
            self.states[-1].on_end()
            del self.states[-1]

    def push_gui_state(self, widget, title=None):
        state = GUIState(widget=widget, title=title)
        self.push_state(state)

    def push_state(self, state):
        self.states.append(state)
        state.init(self)

    def query_cards(self, query: CardQuery, card_set: StudySet) -> StudySet:
        """
        Queries the card/study databases to return a study set.
        """
        assert isinstance(query, CardQuery)
        assert isinstance(card_set, StudySet)
        cards = []
        for card in card_set.get_cards():
            study_data = self.study_database.get_card_study_data(card)
            if query.matches(card, study_data):
                cards.append(card)
        return StudySet(cards=cards)

    def push_study_state(self,
                         card_set: CardSet,
                         card_query=None,
                         study_params=None,
                         scheduler_params=SchedulerParams()):
        """
        Begin a new study state.
        """
        if card_query:
            card_set = self.query_cards(card_query, card_set=card_set)
        if not study_params:
            study_params = StudyParams()
        self.push_state(StudyState(card_set,
                                   study_params=study_params,
                                   scheduler_params=scheduler_params))

    def push_card_list_state(self, card_set):
        self.push_state(CardListState(card_set))

    def push_card_set_edit_state(self, card_set: CardSet, **kwargs):
        self.push_state(GUIState(widget=CardSetEditWidget(card_set, self, **kwargs),
                                 title="Edit Card Set"))

    def push_card_edit_state(self, card: Card, **kwargs):
        widget = CardEditWidget(card, self, **kwargs)
        state = GUIState(widget=widget, title="Edit Card")
        self.push_state(state)
        return widget

    def get_card_word_details(self, card: Card):
        updated = self.word_database.populate_card_details(card, download=True)
        if updated:
            Config.logger.info("Saving word database due to updates from card '{}'".format(card))
            self.save_word_database()
        return card.word

    @property
    def state(self):
        return self.states[-1]

    def save_all_changes(self):
        self.card_database.save_all_changes()
        self.study_database.save_all_changes()

    def save_card_data(self):
        self.card_database.save_card_data()

    def load_card_data(self):
        path = os.path.join(self.root_path, self.card_data_file_name)
        self.card_database.load_card_data(path)

    def save_study_data(self):
        return self.study_database.save()

    def load_study_data(self):
        path = os.path.join(self.root_path, self.save_file_name)
        return self.study_database.load(path, self.card_database)

    def save_word_database(self):
        path = os.path.join(self.root_path, self.word_data_file_name)
        Config.logger.info("Saving word data to: " + path)
        self.word_database.save(path)

    def load_word_database(self):
        path = os.path.join(self.root_path, self.word_data_file_name)
        if os.path.isfile(path):
            Config.logger.info("Loading cooljugator word data from: " + path)
            self.word_database.load(path, source_type=WordSourceEnum.Cooljugator)
        path = os.path.join(self.root_path, self.custom_word_data_file_name)
        if os.path.isfile(path):
            Config.logger.info("Loading custom word data from: " + path)
            self.word_database.load(path, source_type=WordSourceEnum.Custom)
        Config.logger.info("Loading {} words".format(len(self.word_database.words)))

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
                amount = self.joystick.get_axis(input.index)
                if amount < DEAD_ZONE:
                    amount = 0.0
                input.update(amount)
                self.state.buttons[index].update(
                    dt=dt,
                    is_down=input.amount > PRESS_THRESHOLD,
                    is_pressed=input.amount > PRESS_THRESHOLD and input.prev_amount <= PRESS_THRESHOLD)

        self.state.process_input()
        self.state.update(dt)

    def draw(self):
        self.graphics.recache()
        self.graphics.clear(color.WHITE)
        screen_width, screen_height = self.screen.get_size()

        states_to_draw = []
        for state in reversed(self.states):
            states_to_draw.append(state)
            if not state.draw_state_below:
                break
        for state in reversed(states_to_draw):
            # TODO: fade background
            state.draw(self.graphics)
        
        # Draw save status
        kwargs = dict( 
            font=self.__font_status,
            align=Align.TopLeft,
            color=Colors.RED)
        y = screen_height - Config.margin_top + 4
        if self.study_database.is_saving():
            self.graphics.draw_text(
                4, y, text="Saving study data...", **kwargs)
        y += 24
        if self.card_database.is_saving():
            self.graphics.draw_text(
                4, y, text="Saving card data...", **kwargs)
        y += 24
        if self.word_database.is_saving():
            self.graphics.draw_text(
                4, y, text="Saving word data...", **kwargs)
        y += 24
        cooljugator_status = self.cooljugator_thread.get_status()
        if cooljugator_status is not None:
            word_type, name = cooljugator_status
            self.graphics.draw_text(
                4, y, text="Downloading {} info: {}".format(word_type, name), **kwargs)

        # Draw FPS
        fps = self.get_frame_rate()
        self.graphics.draw_text(
            4, 4,
            text="FPS = {}".format(int(round(fps))),
            font=self.__font_fps,
            align=Align.TopLeft,
            color=Colors.RED)

    def __on_key_pressed(self, key, mod, text):
        self.state.on_key_pressed(key, mod, text)

    def __on_key_released(self, key, mod):
        self.state.on_key_released(key, mod)

    def __on_mouse_pressed(self, pos, button):
        self.state.on_mouse_pressed(pos, button)

    def __on_mouse_released(self, pos, button):
        self.state.on_mouse_released(pos, button)


if __name__ == "__main__":
    app = StudyCardsApp()
    app.run()
