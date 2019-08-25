import os
import random
import re
import time
import yaml
from datetime import datetime
from study_tool.card import Card, CardSide, SourceLocation
from study_tool.card_set import CardSet, CardSetPackage, CardGroupMetrics, StudySet
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config
from study_tool.word_database import WordDatabase


TOKEN_DELIMETERS = ["--", "–", "-"]
WORD_TYPE_DICT = {"none": WordType.Other,
                  None: WordType.Other}
for word_type in WordType:
    WORD_TYPE_DICT[word_type.name.lower()] = word_type


class StudyMetrics:
    def __init__(self):
        self.date = datetime.now()
        self.all_metrics = CardGroupMetrics()
        self.word_type_metrics = {}
        for word_type in WordType:
            self.word_type_metrics[word_type] = CardGroupMetrics()

    def get_date_string(self) -> str:
        return self.date.strftime("%Y/%m/%d")

    def serialize(self):
        state = {"date": self.get_date_string(),
                 "all_metrics": self.all_metrics.serialize(),
                 "card_type_metrics": {}}
        for word_type, metrics in self.word_type_metrics.items():
            if metrics.get_total_count() > 0:
                state["card_type_metrics"][word_type.name] = metrics.serialize()
        return state

    def deserialize(self, state):
        self.date = datetime.strptime(state["date"], "%Y/%m/%d")
        self.all_metrics.deserialize(state["all_metrics"])
        for word_type in WordType:
            if word_type.name in state["card_type_metrics"]:
                self.word_type_metrics[word_type].deserialize(
                    state["card_type_metrics"][word_type.name])


class CardDatabase:
    def __init__(self, word_database: WordDatabase):
        self.cards = {}
        self.metrics_history = {}
        self.word_database = word_database
        self.word_to_cards_dict = {}
        self.russian_key_to_card_dict = {}
        self.english_key_to_card_dict = {}
        self.__path_to_card_sets_dict = {}

    def clear(self):
        """Clear all cards."""
        self.cards = {}
        self.metrics_history = {}
        self.word_to_cards_dict = {}
        self.russian_key_to_card_dict = {}
        self.english_key_to_card_dict = {}
        self.__path_to_card_sets_dict = {}

    def has_card(self, card: Card) -> bool:
        return card in self.cards.values()

    def get_card_sets_from_path(self, path: str) -> list:
        return self.__path_to_card_sets_dict.get(path, [])

    def get_card(self, word_type: WordType, english=None, russian=None) -> Card:
        """
        Retreive a card by word type and text.
        """
        if english is not None and russian is not None:
            key = (word_type, AccentedText(russian).text, AccentedText(english).text)
            return self.cards.get(key, None)
        if english is not None:
            key = (word_type, AccentedText(english).text)
            return self.english_key_to_card_dict.get(key, None)
        if russian is not None:
            key = (word_type, AccentedText(russian).text)
            return self.russian_key_to_card_dict.get(key, None)
        raise Exception("Missing english or russian argument")

    def iter_cards(self, word_type=None, english=None, russian=None):
        """
        Iterate cards with the specified fields.
        """
        if english is not None:
            english = AccentedText(english).text.lower()
        if russian is not None:
            russian = AccentedText(russian).text.lower()
        for _, card in self.cards.items():
            if word_type is not None and card.get_word_type() != word_type:
                continue
            if english is not None and card.english.text.lower() != english:
                continue
            if russian is not None and card.russian.text.lower() != russian:
                continue
            yield card
            
    def find_cards_by_word(self, word: str):
        """Find a card by the name of a word."""
        for word_obj in self.word_database.lookup_word(word):
            if word_obj in self.word_to_cards_dict:
                for card in self.word_to_cards_dict[word_obj]:
                    yield card

    def get_study_metrics(self) -> StudyMetrics:
        metrics = StudyMetrics()
        card_set = StudySet(cards=self.cards.values())
        metrics.all_metrics = card_set.get_study_metrics()
        for word_type in WordType:
            card_set = StudySet(cards=(c for c in self.cards.values()
                                       if c.word_type == word_type))
            metrics.word_type_metrics[word_type] = card_set.get_study_metrics()
        return metrics

    def add_card(self, card: Card):
        """Add a new card to the database."""
        word_type = card.get_word_type()

        # Get the Word info associated with this card
        word = None
        for card_word_name in card.get_word_names():
            word = self.word_database.download_word(
                name=card_word_name,
                word_type=card.word_type)
        if word is not None and word.complete:
            self.word_database.populate_card_details(card=card)
        if word is not None:
            if word not in self.word_to_cards_dict:
                self.word_to_cards_dict[word] = [card]
            else:
                self.word_to_cards_dict[word].append(card)

        # Register the card's english and russian identifiers
        ru_key = card.get_russian_key()
        en_key = card.get_english_key()
        key = card.get_key()
        if ru_key in self.russian_key_to_card_dict:
            print(ru_key)
            print(self.russian_key_to_card_dict[ru_key],
                  self.russian_key_to_card_dict[ru_key].source)
            print(card)
            raise Exception("Duplicate card russian: {} '{}'".format(
                word_type.name, card.get_russian().text))
        if en_key in self.english_key_to_card_dict:
            print(en_key)
            print(self.english_key_to_card_dict[en_key],
                  self.english_key_to_card_dict[en_key].source)
            print(card)
            raise Exception("Duplicate card english: {} '{}'".format(
                word_type.name, card.get_english().text))
        if key in self.cards:
            print(card)
            print(self.cards[key])
            raise Exception("Duplicate card: " + repr(key))
        self.russian_key_to_card_dict[ru_key] = card
        self.english_key_to_card_dict[en_key] = card
        self.cards[key] = card
       
    def remove_card(self, card: Card):
        """Remove a card from the card database."""
        # Remove from russian key dict
        found_ru_key = False
        for key, old_card in self.russian_key_to_card_dict.items():
            if old_card == card:
                found_ru_key = True
                del self.russian_key_to_card_dict[key]
                break
        assert found_ru_key

        # Remove from english key dict
        found_en_key = False
        for key, old_card in self.english_key_to_card_dict.items():
            if old_card == card:
                found_en_key = True
                del self.english_key_to_card_dict[key]
                break
        assert found_en_key

        # Remove from key dict
        found_key = False
        for key, old_card in self.cards.items():
            if old_card == card:
                found_key = True
                del self.cards[key]
                break
        assert found_key


    def apply_card_key_change(self, card: Card):
        """Called when a card's key has changed"""
        new_ru_key = card.get_russian_key()
        new_en_key = card.get_english_key()
        new_key = card.get_key()

        # Update russian key dict
        found_ru_key = False
        for old_ru_key, old_card in self.russian_key_to_card_dict.items():
            if old_card == card:
                found_ru_key = True
                if old_ru_key != new_ru_key:
                    Config.logger.info("Russian key change: {} -> {}"
                                       .format(old_ru_key, new_ru_key))
                    del self.russian_key_to_card_dict[old_ru_key]
                    self.russian_key_to_card_dict[new_ru_key] = card
                    break
        assert found_ru_key

        # Update english key dict
        found_en_key = False
        for old_en_key, old_card in self.english_key_to_card_dict.items():
            if old_card == card:
                found_en_key = True
                if old_en_key != new_en_key:
                    Config.logger.info("English key change: {} -> {}"
                                       .format(old_en_key, new_en_key))
                    del self.english_key_to_card_dict[old_en_key]
                    self.english_key_to_card_dict[new_en_key] = card
                    break
        assert found_en_key

        # Update key dict
        found_key = False
        for old_key, old_card in self.cards.items():
            if old_card == card:
                found_key = True
                if old_key != new_key:
                    Config.logger.info("Key change: {} -> {}"
                                       .format(old_key, new_key))
                    del self.cards[old_key]
                    self.cards[new_key] = card
                    break
        assert found_key



    def serialize_card_data(self) -> dict:
        state = []
        for card in self.iter_cards():
            if card.get_fixed_card_set() is None:
                state.append(card.serialize_card_data())
        return state

    def deserialize_card_data(self, state: dict):
        for card_state in state["cards"]:
            card = Card()
            card.deserialize_card_data(card_state)
            self.add_card(card)

    def serialize_study_data(self) -> dict:
        state = {"save_time": time.time(),
                 "cards": [],
                 "metrics": []}
        current_metrics = self.get_study_metrics()
        self.metrics_history[current_metrics.get_date_string()
                             ] = current_metrics
        for date_string, metrics in self.metrics_history.items():
            state["metrics"].append(metrics.serialize())

        for _, card in self.cards.items():
            card_state = card.serialize_study_data()
            card_state["type"] = None if card.word_type is None else card.word_type.name
            card_state["russian"] = card.russian.text
            card_state["english"] = card.english.text
            state["cards"].append(card_state)
        return state

    def deserialize_study_data(self, state: dict):
        for card_state in state["cards"]:
            word_type = card_state["type"]
            if word_type is not None:
                word_type = getattr(WordType, word_type)
            key = (word_type,
                   AccentedText(card_state["russian"]).text,
                   AccentedText(card_state["english"]).text)
            if key in self.cards:
                card = self.cards[key]
                card.deserialize_study_data(card_state)
            else:
                Config.logger.warning("Card not found: " + repr(key))

        self.metrics_history = {}
        for metrics_state in state["metrics"]:
            metrics = StudyMetrics()
            metrics.deserialize(metrics_state)
            self.metrics_history[metrics.get_date_string()] = metrics
        current_metrics = self.get_study_metrics()
        self.metrics_history[current_metrics.get_date_string()
                             ] = current_metrics

    def deserialize_card_set(self, state: dict) -> CardSet:
        state = state["card_set"]
        card_set = CardSet()
        card_set.set_name(AccentedText(state["name"]))
        card_set.key = state["name"].lower().replace(" ", "_")
        for card_state in state["cards"]:
            assert 1 <= len(card_state) <= 3
            word_type = parse_word_type(card_state[0])
            if len(card_state) == 3:
                english = card_state[1]
                russian = card_state[2]
                cards = list(self.iter_cards(word_type=word_type, russian=russian, english=english))
                if not cards:
                    cards = list(self.iter_cards(word_type=word_type, russian=english, english=russian))
                if not cards:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
            elif len(card_state) == 2:
                text = card_state[1]
                cards = list(self.iter_cards(word_type=word_type, russian=text))
                if not cards:
                    cards = list(self.iter_cards(word_type=word_type, english=text))
                if not cards:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
            elif len(card_state) == 1:
                text = card_state[1]
                cards = list(self.iter_cards(russian=text))
                if not cards:
                    cards = list(self.iter_cards(english=text))
                if not cards:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
            else:
                raise Exception(card_state)
            card_set.cards += cards
        return card_set

    def parse_card_text(self, text, split=False):
        attributes = []
        for name in re.findall(r"\@(\S+)", text):
            attribute = CardAttributes(name)
            try:
                attributes.append(attribute)
            except:
                raise Exception("unknown card attribute '{}'".format(name))
        text = re.sub(r"\@\S+", "", text).strip()
        if split:
            text = [AccentedText(x.strip()) for x in text.split("/")]
        else:
            text = AccentedText(text)
        return text, attributes

    def preprocess_lines(self, filename, lines):
        for line_index, line in enumerate(lines):
            if line.startswith("@googledoc"):
                # Include text from a Google Doc
                tokens = line.strip().split()
                document_id = tokens[1]
                Config.logger.info("Loading googledoc: " + document_id)
                document = googledocs.get_document(document_id)
                title = "googledoc[" + document["title"] + "]"
                for line in self.preprocess_lines(title, iter(document["text"].splitlines())):
                    yield line
            else:
                yield filename, line_index + 1, line

    def load_card_set_file(self, path):
        card_set = None
        card_sets = []
        left_side = CardSide.Russian

        def name_to_side(name):
            if name.lower() in ["ru", "russian"]:
                return CardSide.Russian
            elif name.lower() in ["en", "english"]:
                return CardSide.English
            else:
                raise Exception("uknown language: '{}'".format(name))

        with open(path, "r", encoding="utf8") as f:
            filename = path
            line_number = -1
            line = ""
            word_type = WordType.Other
            card_set = None
            split_attributes = None
            card = None
            try:
                for filename, line_number, line in self.preprocess_lines(path, f):
                    line = line.strip()
                    if line.startswith("@"):
                        command = line.split()[0][1:]
                        command_text = (line.split(None, 1)[
                                        1:] or [""])[0].strip()
                        value = line[len(command) + 1:].strip()
                        if command == "name":
                            card_set = CardSet(fixed_card_set=True)
                            card_set.source = SourceLocation(filename=filename,
                                                             line_number=line_number,
                                                             line_text=line)
                            self.__add_card_set_path(card_set, path=filename)
                            card_set.name = AccentedText(value)
                            card_set.key = card_set.name.text.lower().replace(" ", "_")
                            card_sets.append(card_set)
                            left_side = CardSide.Russian
                            split_attributes = None
                        elif command == "key":
                            card_set.key = value
                        elif command == "info":
                            card_set.info = AccentedText(value)
                        elif command == "side":
                            card_set.side = name_to_side(value)
                        elif command == "left":
                            left_side = name_to_side(value)
                        elif command == "split":
                            split_sides = [v.strip() for v in value.split("/")]
                            split_attributes = []
                            for attr_list in split_sides:
                                split_attributes.append([CardAttributes(x.strip())
                                                         for x in attr_list.split()])
                        elif command == "type":
                            word_type = WORD_TYPE_DICT[value.lower()]
                        elif command == "ex" or command == "example":
                            if card is None:
                                raise Exception()
                            card.examples.append(AccentedText(command_text))
                        else:
                            raise Exception(
                                "uknown @ command: '{}'".format(command))
                    elif line.startswith("#"):
                        pass  # ignore comments
                    elif len(line) == 0:
                        pass  # ignore whitespace
                    else:
                        tokens = []
                        for delimeter in TOKEN_DELIMETERS:
                            if delimeter in line:
                                tokens = [t.strip()
                                          for t in line.split(delimeter)]
                                break
                        if len(tokens) == 2:
                            text_l_list, attributes_l = self.parse_card_text(
                                tokens[0], split=True)
                            text_r, attributes_r = self.parse_card_text(
                                tokens[1])
                            if len(text_l_list) > 1:
                                if split_attributes is None:
                                    raise Exception(
                                        "detected '/' with no split configured")
                                if len(split_attributes) != len(text_l_list):
                                    raise Exception("mismatch with split size of {}"
                                                    .format(len(split_attributes)))
                            for split_index, text_l in enumerate(text_l_list):
                                card = Card()
                                card.set_fixed_card_set(card_set)
                                card.source = SourceLocation(filename=filename,
                                                             line_number=line_number,
                                                             line_text=line)
                                card.word_type = word_type
                                card.text[left_side] = text_l
                                card.text[1 - left_side] = text_r
                                card.add_attributes(attributes_l, left_side)
                                card.add_attributes(
                                    attributes_r, 1 - left_side)
                                if split_attributes is not None and len(text_l_list) > 1:
                                    card.add_attributes(attrs=split_attributes[split_index],
                                                        side=1 - left_side)
                                card_set.cards.append(card)
                                card.generate_word_name()
                                self.add_card(card)
                        else:
                            raise Exception("unable to tokenize line")
            except Exception as e:
                Config.logger.error(
                    "Exception: {}-{}: {}".format(filename, line_number, line))
                Config.logger.error("{}: {}".format(type(e).__name__, str(e)))
                raise
                exit(1)
        return sorted(card_sets, key=lambda x: x.name)

    def load_card_package_directory(self, path: str, name: str) -> CardSetPackage:
        package = CardSetPackage(name=name, path=path)

        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)

            if os.path.isdir(file_path):
                # Load a new sub-package
                sub_package = self.load_card_package_directory(
                    path=file_path, name=str(filename))
                if sub_package is not None:
                    sub_package.parent = package
                    package.packages.append(sub_package)

            elif os.path.isfile(file_path):

                if file_path.endswith(".txt"):
                    # Load legacy card set file
                    package.card_sets += self.load_card_set_file(file_path)

                elif file_path.endswith(".yaml"):
                    # Load new card set file
                    with open(file_path, "r", encoding="utf8") as f:
                        state = yaml.safe_load(f)
                        if "card_set" in state:
                            card_set = self.deserialize_card_set(state)
                            if card_set:
                                package.add_card_set(card_set)
                                self.__add_card_set_path(card_set, path=file_path)

        if len(package.packages) == 0 and len(package.card_sets) == 0:
            return None
        package.card_sets.sort(key=lambda x: x.name)
        package.packages.sort(key=lambda x: x.name)
        return package

    def remove_card_set_path(self, path: str):
        """
        Remove a file path from the card set list. This is called when a card
        set is assimilated to YAML, and the old text file is deleted.
        """
        assert path in self.__path_to_card_sets_dict
        for card_set in self.__path_to_card_sets_dict[path]:
            assert card_set.get_file_path() != path
        del self.__path_to_card_sets_dict[path]

    def __add_card_set_path(self, card_set: CardSet, path: str):
        """Associates a card set with a file path."""
        if path not in self.__path_to_card_sets_dict:
            self.__path_to_card_sets_dict[path] = []
        self.__path_to_card_sets_dict[path].append(card_set)
        card_set.set_file_path(path)
