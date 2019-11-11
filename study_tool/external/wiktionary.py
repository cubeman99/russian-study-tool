import threading
import traceback
import yaml
import cmg
import time
from cmg.utilities import ReadWriteLock
from pathlib import Path
from study_tool.config import Config
from study_tool.russian.word import AccentedText
from study_tool.external.wiktionary_term import WiktionaryTerm
from study_tool.external.wiktionary_parser import WiktionaryParser


class Wiktionary:
    """
    Interface to downloading term information from Wiktionary.
    """
    def __init__(self, sounds_dir="data/sounds"):
        self.__name = "wiktionary"
        self.__lock = ReadWriteLock()
        self.__save_lock = threading.Lock()
        self.__parser = WiktionaryParser()
        self.__sounds_dir = Path(sounds_dir)
        self.__terms = {}
        self.__save_path = Path("data/wiktionary.yaml")
        self.__error_terms = set()
        self.__404_terms = set()
        self.__no_word_terms = set()
        self.logger = Config.logger

    def get_term(self, text: str) -> WiktionaryTerm:
        """
        Gets a term by text.
        """
        if isinstance(text, WiktionaryTerm):
            return text
        key = self.__get_term_key(text)
        with self.__lock.acquire_read():
            if key in self.__terms:
                return self.__terms[key]
        return None

    def get_sound(self, term: str) -> cmg.Sound:
        """
        Gets a Sound object for a term.
        """
        print(term)
        path = self.__get_sound_path(term)
        print(path)
        if path.is_file():
            #return cmg.Sound(file=str(path))
            with open(str(path), "rb") as f:
                data = f.read()
            path = "data/sound.ogg"
            with open(path, "wb") as f:
                f.write(data)
            return cmg.Sound(file=path)
            #return cmg.Sound(buffer=data)
        return None

    def clear(self):
        with self.__lock.acquire_write():
            self.__terms.clear()

    def save(self, path=None):
        """
        Saves the Wiktionary data to file.
        """
        with self.__save_lock:
            with self.__lock.acquire_read():
                if path is None:
                    path = self.__save_path
                self.__save_path = path
                terms = list(self.__terms.items())
                terms.sort(key=lambda x: x[0])
                self.logger.info("Saving {} data to {}".format(self.__name, path))
                file_text = ""

                # Save global data
                data = {"version": 1,
                        "save_timestamp": time.time(),
                        "404_terms": list(sorted(self.__404_terms)),
                        "no_word_terms": list(sorted(self.__no_word_terms)),
                        "error_terms": list(sorted(self.__error_terms))}
                file_text += yaml.dump(
                    data, default_flow_style=False, allow_unicode=True)

                # Save term data
                indent = "  "
                file_text += "terms:\n" + indent
                for _, term in terms:
                    key = self.__get_term_key(term)
                    term_data = term.serialize()
                    term_data = {key: term_data}
                    term_yaml = yaml.dump(
                        term_data, default_flow_style=False, allow_unicode=True)
                    file_text += term_yaml.replace("\n", "\n" + indent)

                with open(path, "w", encoding="utf8") as save_file:
                    save_file.write(file_text)

    def load(self, path=None):
        """
        Loads the Wiktionary data to file.
        """
        with self.__lock.acquire_write():
            if path is None:
                path = self.__save_path
            self.__save_path = path
            self.__terms.clear()
            self.logger.info("Loading {} data from {}".format(self.__name, path))
            with open(path, "r", encoding="utf8") as load_file:
                data = yaml.load(load_file, Loader=yaml.CLoader)
                self.__404_terms = set(data["404_terms"])
                self.__no_word_terms = set(data["no_word_terms"])
                self.__error_terms = set(data["error_terms"])
                for key, term_data in data["terms"].items():
                    term = WiktionaryTerm("")
                    term.deserialize(term_data)
                    if term.words:
                        self.__terms[key] = term
        
    def download_sound(self, term: str) -> cmg.Sound:
        """
        Downloads a sound file for a term.
        """
        path = self.__get_sound_path(term)
        key = self.__get_term_key(term)
        if path.is_file():
            return path
        term_object = self.get_term(term)
        if not term_object:
            return None
        url = term_object.get_audio_url()
        if not url:
            return None

        self.logger.info("Downloading {} sound for '{}'".format(self.__name, key))
        import requests
        response = requests.get(url, allow_redirects=True)
        if not response.content.startswith(b"Ogg"):
            return None
        with open(str(path), "wb") as sound_file:
            sound_file.write(response.content)
        return path

    def download_term(self, text: str) -> WiktionaryTerm:
        """
        Downloads information for a term.
        """
        key = self.__get_term_key(text)
        if key in self.__404_terms:
            return None
        if key in self.__error_terms:
            return None
        if key in self.__no_word_terms:
            return None
        self.logger.info("Downloading {} term for '{}'".format(self.__name, key))
        try:
            term = self.__parser.download_term(text)
        except Exception as error:
            self.logger.error("Error parsing {} term: {}".format(self.__name, key))
            with self.__lock.acquire_write():
                self.__error_terms.add(key)
            raise
        if term:
            with self.__lock.acquire_write():
                if not term.words:
                    self.__no_word_terms.add(key)
                    self.logger.error("{} term has no words: {}".format(self.__name, key))
                    return None
                self.__terms[key] = term
        else:
            self.logger.error("{} term 404 not found: {}".format(self.__name, key))
            with self.__lock.acquire_write():
                self.__404_terms.add(key)
        return term

    def __get_sound_url(self, term: str) -> str:
        term_object = self.get_term(term)
        return term.get_audio_url()

    def __get_sound_path(self, term: str) -> Path:
        if isinstance(term, WiktionaryTerm):
            term = term.text
        key = self.__get_term_key(term)
        filename = key.replace(" ", "_") + ".ogg"
        return self.__sounds_dir / filename

    def __get_term_key(self, text: str):
        if isinstance(text, WiktionaryTerm):
            return text.text.text.lower().strip()
        return AccentedText(text).text.lower().strip()


if __name__ == "__main__":
    #word = wiktionary.download_term("открытка")  # Noun
    #word = wiktionary.download_term("хотя бы")  # Conjunction
    #word = wiktionary.download_term("красивый")  # Adjective
    #word = wiktionary.download_term("ум")  # Noun
    #word = wiktionary.download_term("знать")  # Verb
    #word = wiktionary.download_term("бы")  # Particle
    #word = wiktionary.download_term("свой")  # Pronoun

    #text = yaml.dump(word.serialize(), default_flow_style=False, allow_unicode=True).strip()
    #print(text)

    import pygame
    import time
    pygame.mixer.init()

    name = "привет"


    wiktionary = Wiktionary()
    wiktionary.load()
    #wiktionary.clear()
    #wiktionary.download_term(name)
    #wiktionary.download_term("знать")
    #wiktionary.download_term("быть")
    #wiktionary.download_sound(name)
    #sound = wiktionary.get_sound(name)

    from study_tool.word_database import WordDatabase
    from study_tool.russian.word import WordSourceEnum
    word_database = WordDatabase()
    word_database.load("data/word_data.json", source_type=WordSourceEnum.Cooljugator)
    words = sorted(word_database.words.items(), key=lambda x: (x[0][1], x[0][0]))
    total = len(words)
    count = 0
    for index, (key, word) in enumerate(words):
        term = wiktionary.get_term(word.get_name())
        if term:
            wiktionary.download_sound(term.text)
        else:
            print("{}/{}: {}".format(index + 1, total, word.get_name()))
            result = wiktionary.download_term(word.get_name())
            if result:
                count += 1
                if count % 30 == 0:
                    wiktionary.save()
    #wiktionary.save()

    exit()
    #sound.play()
    #time.sleep(1)


    pygame.mixer.quit()
