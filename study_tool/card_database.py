from datetime import datetime
import os
import random
import re
import threading
import time
import yaml
from cmg.event import Event
from cmg.utilities import ReadWriteLock
from study_tool.card import Card
from study_tool.card import SourceLocation
from study_tool.card_set import CardSet
from study_tool.card_set import CardSetType
from study_tool.card_set import CardSetPackage
from study_tool.card_set import CardGroupMetrics
from study_tool.card_set import StudySet
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.config import Config
from study_tool.word_database import WordDatabase


class CardDatabase:
    """
    Database class to store Cards, CardSets, and CardSetPackages
    """

    __TOKEN_DELIMETERS = ["--", "–", "-"]
    __WORD_TYPE_DICT = {"none": WordType.Other,
                      None: WordType.Other}
    for word_type in WordType:
        __WORD_TYPE_DICT[word_type.name.lower()] = word_type


    def __init__(self, word_database: WordDatabase):
        """
        Creates an empty database.
        """
        self.__word_database = word_database
        self.__lock_modify = ReadWriteLock()
        self.__card_data_path = None
        self.__is_saving = False

        # Card data
        self.cards = {}
        self.__word_to_cards_dict = {}
        self.__russian_key_to_card_dict = {}
        self.__english_key_to_card_dict = {}

        # Card set data
        self.__root_package = None
        self.__path_to_card_sets_dict = {}

        # Dirty state
        self.__lock_save = threading.Lock()
        self.__lock_dirty = threading.RLock()
        self.__dirty_cards = set()
        self.__dirty_key_change_cards = set()
        self.__dirty_card_sets = set()

        # Events
        self.card_created = Event(Card)
        self.card_deleted = Event(Card)
        self.card_key_changed = Event(Card)
        self.card_data_changed = Event(Card)
        self.card_added_to_set = Event(Card, CardSet)
        self.card_removed_from_set = Event(Card, CardSet)
        self.card_set_created = Event(CardSet)
        self.card_set_renamed = Event(CardSet)
        
    def is_saving(self) -> bool:
        """Returns True if currently saving the database."""
        return self.__is_saving
        
    def iter_card_sets(self) -> bool:
        """Iterates all card sets."""
        for card_set in self.__root_package.all_card_sets():
            yield card_set

    def get_root_package(self) -> CardSetPackage:
        return self.__root_package

    def has_card(self, card: Card) -> bool:
        with self.__lock_modify.acquire_read():
            return card in self.cards.values()

    def get_orphan_cards(self) -> list:
        card_sets = list(self.__root_package.all_card_sets())
        orphan_cards = []
        for _, card in self.cards.items():
            orphan = True
            for card_set in card_sets:
                if card_set.has_card(card):
                    orphan = False
                    break
            if orphan:
                orphan_cards.append(card)
        return orphan_cards

    def get_card_sets_from_path(self, path: str) -> list:
        with self.__lock_modify.acquire_read():
            return self.__path_to_card_sets_dict.get(path, [])

    def get_card_by_key(self, word_type: WordType, russian=None, english=None) -> Card:
        key = (word_type, russian, english)
        if russian is None and english is None:
            key = word_type
        with self.__lock_modify.acquire_read():
            return self.cards.get(key, None)

    def get_card_by_russian_key(self, key: tuple) -> Card:
        with self.__lock_modify.acquire_read():
            return self.__russian_key_to_card_dict.get(key, None)

    def get_card_by_english_key(self, key: tuple) -> Card:
        with self.__lock_modify.acquire_read():
            return self.__english_key_to_card_dict.get(key, None)

    def get_card(self, word_type: WordType, english=None, russian=None) -> Card:
        """
        Retreive a card by word type and text.
        """
        with self.__lock_modify.acquire_read():
            if english is not None and russian is not None:
                key = (word_type,
                       AccentedText(russian).text.lower(),
                       AccentedText(english).text.lower())
                return self.cards.get(key, None)
            if english is not None:
                key = (word_type, AccentedText(english).text.lower())
                return self.__english_key_to_card_dict.get(key, None)
            if russian is not None:
                key = (word_type, AccentedText(russian).text.lower())
                return self.__russian_key_to_card_dict.get(key, None)
            raise Exception("Missing english or russian argument")

    def iter_cards(self, word_type=None, english=None, russian=None):
        """
        Iterate cards with the specified fields.
        """
        with self.__lock_modify.acquire_read():
            if english is not None:
                english = AccentedText(english).text.lower()
            if russian is not None:
                russian = AccentedText(russian).text.lower()
            for _, card in self.cards.items():
                if word_type is not None and card.get_word_type() != word_type:
                    continue
                if english is not None and card.get_english().text.lower() != english:
                    continue
                if russian is not None and card.get_russian().text.lower() != russian:
                    continue
                yield card

    def find_card(self, word_type=None, english=None, russian=None) -> Card:
        """Returns the first card with the given properties, or None."""
        for card in self.iter_cards(word_type=word_type, english=english, russian=russian):
            return card
        return None
            
    def find_cards_by_word(self, word: str):
        """Find a card by the name of a word."""
        word_obj_list = self.__word_database.lookup_word(word)
        with self.__lock_modify.acquire_read():
            for word_obj in word_obj_list:
                if word_obj in self.__word_to_cards_dict:
                    for card in self.__word_to_cards_dict[word_obj]:
                        yield card

    def clear(self):
        """Clear all cards."""
        with self.__lock_modify.acquire_write():
            self.cards = {}
            self.__word_to_cards_dict = {}
            self.__russian_key_to_card_dict = {}
            self.__english_key_to_card_dict = {}
            self.__path_to_card_sets_dict = {}

    def create_card_set(self, name, file_name: str, package: CardSetPackage) -> CardSet:
        """Creates a new card set."""
        if not file_name.endswith(".yaml"):
            file_name += ".yaml"
        path = os.path.join(package.get_path(), file_name)
        card_set = CardSet(name=name, path=path)
        with self.__lock_modify.acquire_write():
            package.add_card_set(card_set)
            self.__add_card_set_path(card_set, path=path)
        with self.__lock_dirty:
            self.__dirty_card_sets.add(card_set)
        self.card_set_created.emit(card_set)
        return card_set

    def add_card_to_set(self, card: Card, card_set: CardSet):
        """Adds a card to a card set."""
        Config.logger.info("Adding card '{}' to set '{}'".format(card, card_set.get_name()))
        with self.__lock_modify.acquire_write():
            card_set.add_card(card)
            with self.__lock_dirty:
                self.__dirty_card_sets.add(card_set)
            self.card_added_to_set.emit(card, card_set)

    def remove_card_from_set(self, card: Card, card_set: CardSet):
        """Removes card from a card set."""
        Config.logger.info("Removing card '{}' from set '{}'".format(card, card_set.get_name()))
        with self.__lock_modify.acquire_write():
            card_set.remove_card(card)
            with self.__lock_dirty:
                self.__dirty_card_sets.add(card_set)
            self.card_removed_from_set.emit(card, card_set)

    def add_card(self, card: Card, verbose=True):
        """
        Adds a new card to the database.
        """
        with self.__lock_modify.acquire_write():
            if verbose:
                Config.logger.info("Creating new card: " + repr(card))
            if card.get_creation_timestamp() is None:
                card.set_creation_timestamp(time.time())
            word_type = card.get_word_type()

            # Register the card's english and russian identifiers
            ru_key = card.get_russian_key()
            en_key = card.get_english_key()
            key = card.get_key()
            if ru_key in self.__russian_key_to_card_dict:
                print(ru_key)
                print(self.__russian_key_to_card_dict[ru_key],
                      self.__russian_key_to_card_dict[ru_key].source)
                print(card)
                raise Exception("Duplicate card russian: {} '{}'".format(
                    word_type.name, card.get_russian().text))
            if en_key in self.__english_key_to_card_dict:
                print(en_key)
                print(self.__english_key_to_card_dict[en_key],
                      self.__english_key_to_card_dict[en_key].source)
                print(card)
                raise Exception("Duplicate card english: {} '{}'".format(
                    word_type.name, card.get_english().text))
            if key in self.cards:
                print(card)
                print(self.cards[key])
                raise Exception("Duplicate card: " + repr(key))
            self.__russian_key_to_card_dict[ru_key] = card
            self.__english_key_to_card_dict[en_key] = card
            self.cards[key] = card

            # Get the Word info associated with this card
            word = None
            card.generate_word_name()
            for card_word_name in card.get_word_names():
                word = self.__word_database.download_word(
                    name=card_word_name,
                    word_type=card.get_word_type())
            if word is not None:
                if word.is_complete():
                    self.__word_database.populate_card_details(card=card)
                if word not in self.__word_to_cards_dict:
                    self.__word_to_cards_dict[word] = [card]
                else:
                    self.__word_to_cards_dict[word].append(card)

            if not card.is_in_fixed_card_set():
                with self.__lock_dirty:
                    self.__dirty_cards.add(card)
        self.card_created.emit(card)
       
    def delete_card(self, card: Card):
        """
        Delete a card from the card database.
        """
        Config.logger.info("Deleting card: " + repr(card))
        with self.__lock_modify.acquire_write():
            # Unlink related cards
            related_cards = list(card.get_related_cards())
            for related_card in related_cards:
                self.ununlink_related_cards(card, related_card)

            # Remove from russian key dict
            found_ru_key = False
            for key, old_card in self.__russian_key_to_card_dict.items():
                if old_card == card:
                    found_ru_key = True
                    del self.__russian_key_to_card_dict[key]
                    break
            assert found_ru_key

            # Remove from english key dict
            found_en_key = False
            for key, old_card in self.__english_key_to_card_dict.items():
                if old_card == card:
                    found_en_key = True
                    del self.__english_key_to_card_dict[key]
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

            # Remove this card from any card sets
            for card_set in self.iter_card_sets():
                if card_set.has_card(card):
                    self.remove_card_from_set(card, card_set)
        
            with self.__lock_dirty:
                self.__dirty_cards.add(card)
        self.card_deleted.emit(card)

    def update_card(self, original: Card, modified: Card) -> bool:
        """
        Applies modifications to a card.

        :param original: The card to modify.
        :param modified: Card object with the data to apply to the original
                         card.

        :returns: True if there were updates to the card.
        """
        assert original is not modified
        assert not original.is_in_fixed_card_set()
        is_changed = False
        is_key_changed = False

        with self.__lock_modify.acquire_write():
            # Apply any key changes
            key_change_result = self.__apply_card_key_change(
                original=original, modified=modified)
            is_changed = is_changed or key_change_result[0]
            is_key_changed = is_key_changed or key_change_result[1]

            # Update word type
            original.set_word_type(modified.get_word_type())
            assert original.get_word_type() is not None

            # Update card text
            if repr(modified.get_russian()) != repr(original.get_russian()):
                original.set_russian(modified.get_russian())
                original.generate_word_name()
                is_changed = True
            if repr(modified.get_english()) != repr(original.get_english()):
                original.set_english(modified.get_english())
                is_changed = True
        
            # Update card attributes
            old_attrs = set(original.get_attributes())
            new_attrs = set(modified.get_attributes())
            if new_attrs != old_attrs:
                original.set_attributes(new_attrs)
                is_changed = True

            # Update examples
            old_examples = set(repr(x) for x in original.get_examples())
            new_examples = set(repr(x) for x in modified.get_examples())
            if new_examples != old_examples:
                original.set_examples(modified.get_examples())
                is_changed = True

            # Update related cards
            original_related_cards = list(original.get_related_cards())
            modified_related_cards = list(modified.get_related_cards())
            for related_card in original_related_cards:
                if related_card not in modified_related_cards:
                    self.unlink_related_cards(original, related_card)
                    is_changed = True
            for related_card in modified_related_cards:
                if related_card not in original_related_cards:
                    self.link_related_cards(original, related_card)
                    is_changed = True

            if is_changed:
                Config.logger.info("Applied updates to card: " + repr(original))
                with self.__lock_dirty:
                    self.__dirty_cards.add(original)
                    if is_key_changed:
                        self.__dirty_key_change_cards.add(original)

        if is_key_changed:
            self.card_key_changed.emit(original)
        if is_changed:
            self.card_data_changed.emit(original)
        return is_changed
            
    def __apply_card_key_change(self, original: Card, modified: Card) -> tuple:
        """
        Called when a card's key has changed.

        :param card: The Card with the updated key.
        """
        changed = False
        key_changed = False
        old_ru_key = original.get_russian_key()
        new_ru_key = modified.get_russian_key()
        old_en_key = original.get_english_key()
        new_en_key = modified.get_english_key()
        old_key = original.get_key()
        new_key = modified.get_key()

        # Check russian key change
        if old_ru_key != new_ru_key:
            Config.logger.info("Applying card Russian key change: {} -> {}"
                                .format(old_ru_key, new_ru_key))
            if new_ru_key in self.__russian_key_to_card_dict:
                raise KeyError("Duplicate card Russian key: {}".format(new_ru_key))
            changed = True

        # Check english key change
        if old_en_key != new_en_key:
            Config.logger.info("Applying card English key change: {} -> {}"
                                .format(old_en_key, new_en_key))
            if new_en_key in self.__english_key_to_card_dict:
                raise KeyError("Duplicate card English key: {}".format(new_en_key))
            changed = True

        # Check key change
        if old_key != new_key:
            Config.logger.info("Applying card key change: {} -> {}"
                                .format(old_key, new_key))
            if new_key in self.cards:
                raise KeyError("Duplicate card key: {}".format(new_key))
            changed = True
            key_changed = True
           
        # Apply key changes to key dictionaries
        if old_ru_key != new_ru_key:
            del self.__russian_key_to_card_dict[old_ru_key]
            self.__russian_key_to_card_dict[new_ru_key] = original
        if old_en_key != new_en_key:
            del self.__english_key_to_card_dict[old_en_key]
            self.__english_key_to_card_dict[new_en_key] = original
        if old_key != new_key:
            del self.cards[old_key]
            self.cards[new_key] = original
        
        return (changed, key_changed)

    def link_related_cards(self, a: Card, b: Card):
        """Links two cards as related."""
        Config.logger.info("Linking related cards '{a}' and '{b}'"
                           .format(a=repr(a.get_russian()),
                                   b=repr(b.get_russian())))
        a.add_related_card(b)
        b.add_related_card(a)
        with self.__lock_dirty:
            self.__dirty_cards.add(a)
            self.__dirty_cards.add(b)
        self.card_data_changed.emit(a)
        self.card_data_changed.emit(b)
        
    def unlink_related_cards(self, a: Card, b: Card):
        """Un-links two cards as not related."""
        Config.logger.info("Unlinking related cards '{a}' and '{b}'"
                           .format(a=repr(a.get_russian()),
                                   b=repr(b.get_russian())))
        a.remove_related_card(b)
        b.remove_related_card(a)
        with self.__lock_dirty:
            self.__dirty_cards.add(a)
            self.__dirty_cards.add(b)
        self.card_data_changed.emit(a)
        self.card_data_changed.emit(b)

    def update_card_set(self, card_set: CardSet,
                        name: AccentedText, cards: list) -> bool:
        """
        Applies updates to a card set.

        :returns: True if there were updates to the card set.
        """
        is_changed = False
        is_renamed = False
        
        with self.__lock_modify.acquire_write():
            # Update name
            if repr(name) != card_set.get_name():
                card_set.set_name(name)
                is_changed = True
                is_renamed = True

            # Update card list
            old_cards = card_set.get_cards()
            removed_cards = [x for x in old_cards if x not in cards]
            added_cards = [x for x in cards if x not in old_cards]
            if removed_cards or removed_cards or old_cards != cards:
                is_changed = True
            card_set.set_cards(cards)

            if is_changed:
                with self.__lock_dirty:
                    self.__dirty_card_sets.add(card_set)
        if is_renamed:
            self.card_set_renamed.emit(card_set)
        for card in removed_cards:
            self.card_removed_from_set.emit(card, card_set)
        for card in added_cards:
            self.card_added_to_set.emit(card, card_set)
        return is_changed

    def save_all_changes(self):
        """
        Saves all modified data to file, including cards and card sets.
        """
        with self.__lock_modify.acquire_write():
            with self.__lock_dirty:
                # Save card data
                if self.__dirty_key_change_cards:
                    Config.logger.info("Modified key changed cards: " +
                                       str(self.__dirty_key_change_cards))
                if self.__dirty_cards:
                    Config.logger.info("Modified cards: " + str(self.__dirty_cards))
                    self.save_card_data()
                self.__dirty_cards.clear()

                # Any card sets which contain any cards whose key changed must
                # also be saved
                for card_set in self.__root_package.all_card_sets():
                    for card in self.__dirty_key_change_cards:
                        if card_set.has_card(card):
                            self.__dirty_card_sets.add(card_set)

                # Save card sets
                dirty_sets = list(self.__dirty_card_sets)
                for card_set in dirty_sets:
                    self.save_card_set(card_set)
                self.__dirty_card_sets.clear()
        
    def save_card_data(self, path=None):
        """
        Saves card data to a YAML file.
        """
        if path is None:
            path = self.__card_data_path
        assert path is not None
        Config.logger.info("Saving card data to: " + path)
        
        with self.__lock_save:
            with self.__lock_modify.acquire_read():
                self.__is_saving = True

                # Serialize the card data
                state = self.__serialize_card_data()

                # Verify the serialized data can be deserialized
                #self.__deserialize_card_data({"cards": state})

                # Save to temp file first
                temp_path = path + ".temp"
                with open(temp_path, "wb") as f:
                    f.write(b"cards:\n")
                    for card in state:
                        f.write(b"- ")
                        yaml.dump(card, f, encoding="utf8",
                                  allow_unicode=True, default_flow_style=True,
                                  Dumper=yaml.CDumper)
                os.remove(path)
                os.rename(temp_path, path)
                with self.__lock_dirty:
                    self.__dirty_cards.clear()

                self.__is_saving = False

    def load_card_data(self, path: str):
        """
        Loads card data from a YAML file.
        """
        Config.logger.info("Loading card data from: " + path)
        with self.__lock_modify.acquire_write():
            self.__card_data_path = path
            with open(path, "r", encoding="utf8") as f:
                state = yaml.load(f, Loader=yaml.CLoader)
                self.__deserialize_card_data(state)
            with self.__lock_dirty:
                self.__dirty_cards.clear()
                    
    def load_card_sets(self, path: str) -> CardSetPackage:
        """
        Loads the root card package.
        """
        Config.logger.info("Loading card sets from directory: " + path)
        with self.__lock_modify.acquire_write():
            self.__root_package = self.__load_card_package_directory(
                path=path, name="words")
            with self.__lock_dirty:
                self.__dirty_card_sets.clear()
            return self.__root_package

    def save_card_set(self, card_set: CardSet, path=None):
        """
        Save a single card set file to a YAML file.
        """
        Config.logger.info("Saving card set '{}'".format(card_set.get_name()))
        with self.__lock_save:
            self.__is_saving = True
            with self.__lock_modify.acquire_read():
                if path is None:
                    path = card_set.get_file_path()
                    assert path is not None
        
                state = card_set.serialize()

                cards_state = state["card_set"]["cards"]
                del state["card_set"]["cards"]
                with open(path, "wb") as opened_file:
                    yaml.dump(state, opened_file, encoding="utf8",
                              allow_unicode=True, default_flow_style=False,
                              Dumper=yaml.CDumper)
                    if not cards_state:
                        opened_file.write(b"  cards: []")
                    else:
                        opened_file.write(b"  cards:\n")
                        for card_state in cards_state:
                            opened_file.write(b"    - ")
                            yaml.dump(
                                card_state, opened_file, encoding="utf8",
                                allow_unicode=True, default_flow_style=True,
                                Dumper=yaml.CDumper)
                
            card_set.set_fixed_card_set(False)
            card_set.set_file_path(path)

            with self.__lock_dirty:
                if card_set in self.__dirty_card_sets:
                    self.__dirty_card_sets.remove(card_set)
            self.__is_saving = False

    def __serialize_card_data(self) -> dict:
        """Serialize card data."""
        state = []
        for card in self.iter_cards():
            if not card.is_in_fixed_card_set():
                state.append(card.serialize_card_data())
        return state

    def __deserialize_card_data(self, state: dict):
        """Deserialize card data."""
        card_list = []
        for card_state in state["cards"]:
            card = Card()
            card.deserialize_card_data(card_state)
            card_list.append(card)
            self.add_card(card, verbose=False)
            
        # Deserialize and link related cards
        for index, card_state in enumerate(state["cards"]):
            card = card_list[index]
            if "rel" in card_state:
                for related_card_key in card_state["rel"]:
                    related_type = parse_word_type(related_card_key[0].lower(), strict=True)
                    related_russian = related_card_key[1]
                    related_english = related_card_key[2]
                    related_card = self.get_card(word_type=related_type,
                                                 russian=related_russian,
                                                 english=related_english)
                    if not related_card:
                        raise Exception("Unable to find related card: " +
                                        str(related_card_key))
                    card.add_related_card(related_card)
                    related_card.add_related_card(card)

    def __load_card_package_directory(self, path: str, name: str) -> CardSetPackage:
        package = CardSetPackage(name=name, path=path)

        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)

            if os.path.isdir(file_path):
                # Load a new sub-package
                sub_package = self.__load_card_package_directory(
                    path=file_path, name=str(filename))
                if sub_package is not None:
                    sub_package.parent = package
                    package.packages.append(sub_package)

            elif os.path.isfile(file_path):

                if file_path.endswith(".txt"):
                    # Load legacy card set file
                    package.card_sets += self.__load_card_set_file(file_path)

                elif file_path.endswith(".yaml"):
                    # Load new card set file
                    with open(file_path, "r", encoding="utf8") as f:
                        state = yaml.load(f, Loader=yaml.CLoader)
                        if "card_set" in state:
                            card_set = self.__deserialize_card_set(state)
                            if card_set:
                                package.add_card_set(card_set)
                                self.__add_card_set_path(card_set, path=file_path)

        if len(package.packages) == 0 and len(package.card_sets) == 0:
            return None
        package.card_sets.sort(key=lambda x: x.name)
        package.packages.sort(key=lambda x: x.name)
        return package

    def __deserialize_card_set(self, state: dict) -> CardSet:
        """Deserialize card set data."""
        state = state["card_set"]
        card_set = CardSet(name=state["name"])
        card_set.key = state["name"].lower().replace(" ", "_")
        if "type" in state:
            card_set.set_card_set_type(gatrattr(CardSetType, state["type"]))

        for card_state in state.get("cards", []):
            assert 1 <= len(card_state) <= 3
            word_type = parse_word_type(card_state[0])
            if len(card_state) == 3:
                russian = card_state[1]
                english = card_state[2]
                key = (word_type, russian.lower(), english.lower())
                card = self.cards.get(key, None)
                if card is None:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
                card.generate_word_name()
                card_set.add_card(card)
            elif len(card_state) == 2:
                text = card_state[1]
                cards = list(self.iter_cards(word_type=word_type, russian=text))
                if not cards:
                    cards = list(self.iter_cards(word_type=word_type, english=text))
                if not cards:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
                card_set.cards += cards
            elif len(card_state) == 1:
                text = card_state[1]
                cards = list(self.iter_cards(russian=text))
                if not cards:
                    cards = list(self.iter_cards(english=text))
                if not cards:
                    raise Exception("Cannot find card {} in database"
                                    .format(card_state))
                card_set.cards += cards
            else:
                raise Exception(card_state)
        return card_set
    
    def __load_card_set_file(self, path):
        card_set = None
        card_sets = []

        with open(path, "r", encoding="utf8") as f:
            filename = path
            line_number = -1
            line = ""
            card_set = None
            word_type = None
            card = None
            try:
                for filename, line_number, line in self.__preprocess_lines(path, f):
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
                        elif command == "type":
                            word_type = self.__WORD_TYPE_DICT[value.lower()]
                        elif command == "ex" or command == "example":
                            assert card is not None
                            card.add_example(command_text)
                        else:
                            raise Exception(
                                "uknown @ command: '{}'".format(command))
                    elif line.startswith("#"):
                        pass  # ignore comments
                    elif len(line) == 0:
                        pass  # ignore whitespace
                    else:
                        tokens = []
                        for delimeter in self.__TOKEN_DELIMETERS:
                            if delimeter in line:
                                tokens = [t.strip()
                                          for t in line.split(delimeter)]
                                break
                        if len(tokens) == 2:
                            assert word_type is not None
                            russian, attributes_left = self.__parse_card_text(tokens[0])
                            english, attributes_right = self.__parse_card_text(tokens[1])
                            card = Card(russian=russian,
                                        english=english,
                                        word_type=word_type)
                            card.set_fixed_card_set(card_set)
                            card.source = SourceLocation(filename=filename,
                                                         line_number=line_number,
                                                         line_text=line)
                            card.add_attributes(attributes_left)
                            card.add_attributes(attributes_right)
                            card_set.add_card(card)
                            card.generate_word_name()
                            self.add_card(card, verbose=False)
                        else:
                            raise Exception("unable to tokenize line")
            except Exception as e:
                Config.logger.error(
                    "Exception: {}-{}: {}".format(filename, line_number, line))
                Config.logger.error("{}: {}".format(type(e).__name__, str(e)))
                raise
                exit(1)
        return sorted(card_sets, key=lambda x: x.name)
    
    def __parse_card_text(self, text):
        attributes = []
        for name in re.findall(r"\@(\S+)", text):
            attribute = CardAttributes(name)
            try:
                attributes.append(attribute)
            except:
                raise Exception("unknown card attribute '{}'".format(name))
        text = re.sub(r"\@\S+", "", text).strip()
        text = AccentedText(text)
        return text, attributes

    def __preprocess_lines(self, filename, lines):
        for line_index, line in enumerate(lines):
            if line.startswith("@googledoc"):
                # Include text from a Google Doc
                tokens = line.strip().split()
                document_id = tokens[1]
                Config.logger.info("Loading googledoc: " + document_id)
                document = googledocs.get_document(document_id)
                title = "googledoc[" + document["title"] + "]"
                for line in self.__preprocess_lines(title, iter(document["text"].splitlines())):
                    yield line
            else:
                yield filename, line_index + 1, line

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
