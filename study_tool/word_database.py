import json
import shutil
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.card import *
from study_tool.card_attributes import *
from study_tool.config import Config

WORD_TYPE_TYPES = {
    WordType.Verb: Verb,
    WordType.Noun: Noun,
    WordType.Adjective: Adjective,
}


class WordDatabase:
    def __init__(self):
        self.words = {}
        self.word_dictionary = {}
        self.word_dictionary_lax = {}
        self.cooljugator_404_words = []

    def get_word(self, name: str, word_type: WordType) -> Word:
        """
        Looks up a Word object by its word type and dictionary form.
        """
        key = (word_type, name.text)
        if key in self.words:
            return self.words[key]
        elif word_type not in WORD_TYPE_TYPES:
            return self.__create_default_word(name=name, word_type=word_type)
        return None

    def lookup_word(self, word: str) -> Word:
        """Looks up a Word object by text, in any form."""
        key = word.lower()
        word_objs = []
        if key in self.word_dictionary:
            word_objs += self.word_dictionary[key]
        if "ё" not in key and key in self.word_dictionary_lax:
            word_objs += self.word_dictionary_lax[key]
        return word_objs

    def download_word(self, name: AccentedText, word_type: WordType) -> Word:
        """
        Download word info from Cooljugator.
        :returns: the Word object
        """
        key = (word_type, name.text)
        if key in self.words and self.words[key].complete:
            return self.words[key]

        if self.__is_word_404_on_cooljugator(word_type=word_type, name=name.text):
            if key not in self.words:
                self.words[key] = self.__create_default_word(
                    name=name, word_type=word_type)
            return self.words[key]

        if key in self.words:
            del self.words[key]
        if word_type == WordType.Verb:
            word = self.__add_verb(name)
        elif word_type == WordType.Noun:
            word = self.__add_noun(name)
        elif word_type == WordType.Adjective:
            word = self.__add_adjective(name)
        else:
            self.words[key] = self.__create_default_word(
                name=name, word_type=word_type)
            return self.words[key]

        if word is not None and word.word_type != word_type:
            raise Exception(word.word_type)
        return word

    def get_word_from_card(self, card):
        return self.get_word(name=card.word_name,
                             word_type=card.word_type)

    def populate_card_details(self, card, download=False) -> bool:
        if card.word_type is not None:
            word = self.get_word(name=card.word_name,
                                 word_type=card.word_type)
            if download and (word is None or not word.complete):
                word = self.download_word(name=card.word_name,
                                          word_type=card.word_type)
            if word is None:
                word = self.__create_default_word(card.word_name,
                                                  word_type=card.word_type,
                                                  meaning=card.english)
            if word is not None:
                if isinstance(word, Verb):
                    if word.aspect == Aspect.Imperfective:
                        card.add_attribute(
                            CardAttributes.Imperfective, side=CardSide.English)
                    elif word.aspect == Aspect.Perfective:
                        card.add_attribute(
                            CardAttributes.Perfective, side=CardSide.English)
                    suffix = word.classify_conjugation()
                    if suffix is not None:
                        card.add_attribute(
                            VERB_SUFFIX_TO_ATTRIBUTE[suffix], side=CardSide.English)
                elif isinstance(word, Noun):
                    if CardAttributes.Indeclinable in card.attributes[CardSide.Russian]:
                        word.gender = None
                    else:
                        for gender, attr in GENDER_TO_ATTRIBUTE.items():
                            if attr in card.attributes[CardSide.Russian]:
                                word.gender = gender
                        if word.gender is not None:
                            card.add_attribute(GENDER_TO_ATTRIBUTE[word.gender],
                                               side=CardSide.Russian)
                    if word.gender is None:
                        word.indeclinable = True
                        card.add_attribute(CardAttributes.Indeclinable,
                                           side=CardSide.Russian)
                card.word = word
                return True
        return False

    def add_word(self, word) -> Word:
        key = (word.word_type, word.name.text)

        if key in self.words:
            raise Exception("Duplicate word: {} ({})".format(
                word.name.text, word.word_type.name))
        for form in word.get_all_forms():
            self.__add_to_dictionary(form=form, word=word)
        self.words[key] = word
        return word

    def save(self, path):
        word_data = self.serialize()
        temp_path = path + ".temp"
        with open(temp_path, "w", encoding="utf8") as f:
            json.dump(word_data, f, indent=2,
                      sort_keys=True, ensure_ascii=False)
        shutil.move(temp_path, path)

    def load(self, path):
        with open(path, "r", encoding="utf8") as f:
            word_data = json.load(f)
        self.deserialize(word_data)

    def serialize(self):
        data = {
            "words": [],
            "cooljugator": {
                "404_words": {}
            }
        }
        for name, word in self.words.items():
            if word is not None and word.word_type in WORD_TYPE_TYPES and word.complete:
                word_data = Word.serialize(word)
                data["words"].append(word_data)
        bad_word_data = data["cooljugator"]["404_words"]
        for word_type, word in self.cooljugator_404_words:
            if word_type.name not in bad_word_data:
                bad_word_data[word_type.name] = []
            bad_word_data[word_type.name].append(word)
        return data

    def deserialize(self, data):
        self.words = {}
        for word_data in data["words"]:
            word_type = getattr(WordType, word_data["type"])
            word = None
            if word_type == WordType.Verb:
                word = Verb()
            elif word_type == WordType.Adjective:
                word = Adjective()
            elif word_type == WordType.Noun:
                word = Noun()
            Word.deserialize(word, word_data)
            word.deserialize(word_data[word_type.name])
            self.add_word(word)
        for word_type_name, word_list in data["cooljugator"]["404_words"].items():
            word_type = getattr(WordType, word_type_name)
            for name in word_list:
                self.__note_cooljugator_404_word(
                    word_type=word_type, name=name)

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def __add_to_dictionary(self, form: AccentedText, word: Word):
        """Add a word form to the lookup dictionary."""
        form = form.text
        if form not in self.word_dictionary:
            self.word_dictionary[form] = [word]
        else:
            self.word_dictionary[form].append(word)
        if "ё" in form:
            form = form.replace("ё", "е")
            if form not in self.word_dictionary_lax:
                self.word_dictionary_lax[form] = [word]
            else:
                self.word_dictionary_lax[form].append(word)

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

    def __add_verb(self, infinitive) -> Verb:
        from study_tool.external import cooljugator
        Config.logger.info("Downloading verb info for " + infinitive)
        verb = cooljugator.get_verb_info(infinitive)
        if verb is not None:
            self.add_word(verb)
        else:
            self.__note_cooljugator_404_word(
                WordType.Verb, infinitive.text)
        return verb

    def __add_noun(self, dictionary_form) -> Noun:
        from study_tool.external import cooljugator
        Config.logger.info("Downloading noun info for " + dictionary_form)
        noun = cooljugator.get_noun_info(dictionary_form)
        if noun is not None:
            self.add_word(noun)
        else:
            self.__note_cooljugator_404_word(
                WordType.Noun, dictionary_form.text)
        return noun

    def __add_adjective(self, dictionary_form) -> Adjective:
        from study_tool.external import cooljugator
        Config.logger.info("Downloading adjective info for " + dictionary_form)
        adjective = cooljugator.get_adjective_info(dictionary_form)
        if adjective is not None:
            self.add_word(adjective)
        else:
            self.__note_cooljugator_404_word(
                WordType.Adjective, dictionary_form.text)
        return adjective

    def __note_cooljugator_404_word(self, word_type: WordType, name: str):
        self.cooljugator_404_words.append((word_type, name))

    def is_word_404_on_cooljugator(self, name: str, word_type: WordType) -> bool:
        return self.__is_word_404_on_cooljugator(name=name, word_type=word_type)

    def __is_word_404_on_cooljugator(self, name: str, word_type: WordType) -> bool:
        return (word_type, name) in self.cooljugator_404_words
