import requests
import threading
import time
import traceback
import re
import yaml
from study_tool.config import Config
from study_tool.russian.word import AccentedText, has_russian_letters
from study_tool.russian.verb import VerbConjugation
from study_tool.russian.noun import NounDeclension
from study_tool.russian.adjective import AdjectiveDeclension
from study_tool.russian.types import WordType, Plurality, Case, Person, Aspect, Gender, Participle, Tense
from study_tool.russian import types
from study_tool.russian.story import Story, Chapter


class WiktionaryTerm:
    """
    Data representing a single page on Wiktionary for a term.
    """
    def __init__(self, text: AccentedText):
        self.text = AccentedText(text)
        self.etymology = AccentedText()
        self.words = {}
        self.audio_sources = {}
        self.download_timestamp = time.time()

    def get_audio_url(self, extension="ogg") -> str:
        return self.audio_sources.get(extension, None)

    def get_word_data(self, word_type: WordType):
        return self.words.get(word_type, None)

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "text": self.text.raw,
            "download_timestamp": self.download_timestamp,
            "etymology": self.etymology.raw,
            "words": {},
        }
        if self.audio_sources:
            data["audio_sources"] = {}
            for extension, url in self.audio_sources.items():
                data["audio_sources"][extension] = url
        for word_type, word_data in self.words.items():
            data["words"][word_type.name.lower()] = word_data.serialize()
        return data

    def deserialize(self, data: dict):
        """Deserialize the state of this object from a dictionary."""
        self.text = AccentedText(data["text"])
        self.download_timestamp = data["download_timestamp"]
        self.etymology = AccentedText(data["etymology"])
        self.words.clear()
        self.audio_sources.clear()
        self.audio_sources.update(data.get("audio_sources", {}))
        for word_type_name, word_data in data.get("words", {}).items():
            word_type = types.parse_word_type(word_type_name)
            word = WiktionaryWordData(word_type=word_type)
            word.deserialize(word_data)
            self.words[word_type] = word


class WiktionaryWordData:
    """
    Data representing information for a single word type for a term.
    """
    def __init__(self, word_type: WordType, text: AccentedText = ""):
        self.text = AccentedText(text)
        self.word_type = word_type
        self.definitions = []
        self.related_terms = []
        self.derived_terms = []
        self.synonyms = []
        self.antonyms = []
        self.etymology = AccentedText()

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "text": self.text.raw,
            "definitions": [x.serialize() for x in self.definitions],
        }
        if self.etymology.raw:
            data["etymology"] = self.etymology.raw,
        if self.related_terms:
            data["related_terms"] = [term.raw for term in self.related_terms]
        if self.derived_terms:
            data["derived_terms"] = [term.raw for term in self.derived_terms]
        if self.synonyms:
            data["synonyms"] = [term.raw for term in self.synonyms]
        if self.antonyms:
            data["antonyms"] = [term.raw for term in self.antonyms]
        return data

    def deserialize(self, data: dict):
        """Deserialize the state of this object from a dictionary."""
        self.text = AccentedText(data["text"])
        self.etymology = AccentedText(data.get("etymology", ""))
        self.related_terms = [AccentedText(term) for term in data.get("related_terms", [])]
        self.derived_terms = [AccentedText(term) for term in data.get("derived_terms", [])]
        self.synonyms = [AccentedText(term) for term in data.get("synonyms", [])]
        self.antonyms = [AccentedText(term) for term in data.get("antonyms", [])]
        self.definitions = []
        for definition_data in data.get("definitions", []):
            definition = WiktionaryWordDefinition()
            definition.deserialize(definition_data)
            self.definitions.append(definition)

class WiktionaryVerbData(WiktionaryWordData):
    def __init__(self, text: AccentedText):
        super().__init__(text=text, word_type=WordType.Verb)
        self.conjugation = VerbConjugation()
        self.aspect = Aspect.Imperfective
        self.transitive = False
        self.reflexive = False
        self.counterparts = []
        
    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = super().serialize()
        data["verb"] = {
            "aspect": types.get_aspect_short_form_name(self.aspect),
            "transitive": self.transitive,
            "reflexive": self.reflexive,
            "conjugation": self.conjugation.serialize()
        }
        if self.counterparts:
            data["verb"]["counterparts"] = [x.raw for x in self.counterparts]
        return data


class WiktionaryNounData(WiktionaryWordData):
    def __init__(self, text: AccentedText):
        super().__init__(text=text, word_type=WordType.Noun)
        self.declension = NounDeclension()
        
    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = super().serialize()
        data["noun"] = {"declension": self.declension.serialize()}
        return data


class WiktionaryAdjectiveData(WiktionaryWordData):
    def __init__(self, text: AccentedText):
        super().__init__(text=text, word_type=WordType.Adjective)
        self.declension = AdjectiveDeclension()
        
    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = super().serialize()
        data["adjective"] = {"declension": self.declension.serialize()}
        return data


class WiktionaryPronounData(WiktionaryWordData):
    def __init__(self, text: AccentedText):
        super().__init__(text=text, word_type=WordType.Pronoun)
        self.declension = AdjectiveDeclension()
        
    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = super().serialize()
        data["pronoun"] = {"declension": self.declension.serialize()}
        return data

class WiktionaryWordDefinition:
    """
    Data representing a definition for a word.
    """
    def __init__(self):
        self.definition = AccentedText()
        self.examples = []

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "definition": self.definition.raw,
        }
        if self.examples:
            data["examples"] = []
            for russian, english in self.examples:
                data["examples"].append({
                    "ru": russian.raw,
                    "en": english.raw})
        return data

    def deserialize(self, data: dict):
        """Deserialize the state of this object from a dictionary."""
        self.definition = AccentedText(data["definition"])
        self.etymology = AccentedText(data.get("etymology", ""))
        self.related_terms = [AccentedText(term) for term in data.get("related_terms", [])]
        self.derived_terms = [AccentedText(term) for term in data.get("derived_terms", [])]
        self.synonyms = [AccentedText(term) for term in data.get("synonyms", [])]
        self.antonyms = [AccentedText(term) for term in data.get("antonyms", [])]
        self.examples = []
        for example_data in data.get("examples", []):
            self.examples.append((AccentedText(example_data["ru"]),
                                  AccentedText(example_data["en"])))
