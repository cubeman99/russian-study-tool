import json
import os
import shutil
import threading
import yaml
from cmg.event import Event
from cmg.utilities.read_write_lock import ReadWriteLock
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.word import WordSourceEnum
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.card_attributes import *
from study_tool.config import Config
from study_tool.external.cooljugator import Cooljugator


class WordDatabase:
    """
    Database class to store Words.
    """

    # WordType to class
    __WORD_TYPE_TYPES = {
        WordType.Verb: Verb,
        WordType.Noun: Noun,
        WordType.Adjective: Adjective,
    }

    def __init__(self):
        """
        Creates an empty database.
        """
        self.__lock = ReadWriteLock()
        self.words = {}
        self.__word_dictionary = {}
        self.__word_dictionary_lax = {}
        self.__cooljugator = Cooljugator()
        self.__lock_save = threading.Lock()
        self.__is_saving = False

        # Events
        self.word_created = Event(Word)

    def is_saving(self) -> bool:
        """Returns True if currently saving the database."""
        return self.__is_saving

    def get_word(self, name: str, word_type: WordType) -> Word:
        """
        Looks up a Word object by its word type and dictionary form.
        """
        key = self.__get_word_key(word_type=word_type, name=name)
        with self.__lock.acquire_read():
            if key in self.words:
                return self.words[key]
        if word_type not in self.__WORD_TYPE_TYPES:
            return self.__create_default_word(name=name, word_type=word_type)
        return None

    def get_word_from_card(self, card: Card) -> Word:
        return self.get_word(name=card.word_name,
                             word_type=card.get_word_type())

    def lookup_word(self, word: str) -> Word:
        """Looks up a Word object by text, in any form."""
        key = word.lower()
        word_objs = []
        with self.__lock.acquire_read():
            if key in self.__word_dictionary:
                word_objs += self.__word_dictionary[key]
            if "ё" not in key and key in self.__word_dictionary_lax:
                word_objs += self.__word_dictionary_lax[key]
            return word_objs

    def download_word(self, name: AccentedText, word_type: WordType,
                      default_on_fallback=True) -> Word:
        """
        Download a word from Cooljugator.

        :returns: the Word object
        """
        key = self.__get_word_key(word_type=word_type, name=name)
        with self.__lock.acquire_read():
            if key in self.words and self.words[key].is_complete():
                return self.words[key]

        with self.__lock.acquire_write():
            word = self.__cooljugator.download_word_info(
                word_type=word_type, name=name)
            if word:
                self.add_word(word, replace=True)
            elif key in self.words:
                return self.words[key]
            elif default_on_fallback:
                word = self.__create_default_word(name=name, word_type=word_type)
            if word is not None and word.word_type != word_type:
                raise Exception(word.word_type)
            return word

    def populate_card_details(self, card, download=False) -> bool:
        """
        Populates card data with information from a Word.
        """
        with self.__lock.acquire_write():
            updated = False
            if card.get_word_type() is not None:
                word = self.get_word(name=card.word_name,
                                     word_type=card.get_word_type())

                # Attempt to download details about the word
                if download and (word is None or not word.is_complete()):
                    word = self.download_word(name=card.word_name,
                                              word_type=card.get_word_type(),
                                              default_on_fallback=False)
                    updated = word is not None

                # Create a default word with auto-conjugation
                if word is None:
                    word = self.__create_default_word(card.word_name,
                                                      word_type=card.get_word_type(),
                                                      meaning=card.get_english())
                    updated = word is not None

                # Update the card data from the word details
                if word is not None:
                    if isinstance(word, Verb):
                        if word.aspect == Aspect.Imperfective:
                            card.add_attribute(CardAttributes.Imperfective)
                        elif word.aspect == Aspect.Perfective:
                            card.add_attribute(CardAttributes.Perfective)
                        suffix = word.classify_conjugation()
                        if suffix is not None:
                            card.add_attribute(VERB_SUFFIX_TO_ATTRIBUTE[suffix])
                    elif isinstance(word, Noun):
                        if CardAttributes.Indeclinable in card.get_attributes():
                            word.gender = None
                        else:
                            for gender, attr in GENDER_TO_ATTRIBUTE.items():
                                if attr in card.get_attributes():
                                    word.gender = gender
                            if word.gender is not None:
                                card.add_attribute(GENDER_TO_ATTRIBUTE[word.gender])
                        if word.gender is None:
                            word.indeclinable = True
                            card.add_attribute(CardAttributes.Indeclinable)
                    card.word = word
            return updated

    def add_word(self, word: Word, replace=False) -> Word:
        """Adds a new word the database."""
        key = word.get_key()
        with self.__lock.acquire_write():
            if not replace and key in self.words:
                raise Exception("Duplicate word: {} ({})"
                                .format(word.name.text, word.word_type.name))
            for form in word.get_all_forms():
                self.__add_to_dictionary(form=form, word=word)
            self.words[key] = word
        self.word_created.emit(word)
        return word

    def save(self, path: str):
        """Save word data to a file."""
        with self.__lock_save:
            self.__is_saving = True
            word_data = self.serialize()
            temp_path = path + ".temp"
            with open(temp_path, "w", encoding="utf8") as f:
                json.dump(word_data, f, indent=2,
                            sort_keys=True, ensure_ascii=False)
            os.remove(path)
            os.rename(temp_path, path)
            self.__is_saving = False

    def load(self, path: str, source_type: WordSourceEnum):
        """Load word data from a file."""
        with self.__lock_save:
            with open(path, "r", encoding="utf8") as f:
                if path.endswith("yaml"):
                    word_data = yaml.load(f, Loader=yaml.CLoader)
                elif path.endswith("json"):
                    word_data = json.load(f)
                else:
                    raise Exception(path)
            self.deserialize(word_data, source_type=source_type)

    def serialize(self) -> dict:
        """Serialize word data."""
        with self.__lock.acquire_read():
            data = {"words": []}

            # Serialize word data
            for _, word in sorted(self.words.items(), key=lambda x: (x[0][1], x[0][0])):
                if (word.get_word_type() in self.__WORD_TYPE_TYPES and
                        word.get_source() == WordSourceEnum.Cooljugator):
                    word_data = Word.serialize(word)
                    data["words"].append(word_data)

            data["cooljugator"] = self.__cooljugator.serialize()

            return data

    def deserialize(self, data: dict, source_type: WordSourceEnum):
        """
        Deserialize word data.

        :param data: The dictionary of serialized word data.
        :param source_type: Source type for the words.
        """
        with self.__lock.acquire_write():
            # Deserialize list of words with download errors
            if "cooljugator" in data:
                self.__cooljugator.deserialize(data["cooljugator"])

            # Deserialize word data
            for word_data in data["words"]:
                word_type = getattr(WordType, word_data["type"])
                word = self.__WORD_TYPE_TYPES.get(word_type, Word)()
                Word.deserialize(word, word_data)
                if word_type.name in word_data:
                    word.deserialize(word_data[word_type.name])
                word.set_source(source_type)
                self.add_word(word)

    def __add_to_dictionary(self, form: AccentedText, word: Word):
        """Add a word form to the lookup dictionary."""
        form = form.text
        if form not in self.__word_dictionary:
            self.__word_dictionary[form] = [word]
        else:
            self.__word_dictionary[form].append(word)
        if "ё" in form:
            form = form.replace("ё", "е")
            if form not in self.__word_dictionary_lax:
                self.__word_dictionary_lax[form] = [word]
            else:
                self.__word_dictionary_lax[form].append(word)

    def __create_default_word(self, name: str, word_type: WordType, meaning=""):
        if word_type == WordType.Adjective:
            word = Adjective()
            word.name = AccentedText(name)
            word.auto_generate_forms()
        else:
            word = Word()
            word.word_type = word_type
            word.name = AccentedText(name)
        word.meaning = AccentedText(meaning)
        self.add_word(word)
        return word

    def __get_word_key(self, word_type, name):
        return (word_type, AccentedText(name).text.lower().replace("ё", "е"))
