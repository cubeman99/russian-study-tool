import requests
import threading
import traceback
import re
from study_tool.russian.types import Aspect
from study_tool.russian.types import Case
from study_tool.russian.types import Gender
from study_tool.russian.types import Person
from study_tool.russian.types import Plurality
from study_tool.russian.types import Tense
from study_tool.russian.types import WordType
from study_tool.russian.word import AccentedText
from study_tool.russian.word import Word
from study_tool.russian.word import WordSourceEnum
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.russian.adjective import Adjective
from study_tool.config import Config

class Cooljugator404Exception(Exception):
    pass

class Cooljugator:

    # Characters in examples that are wrong
    russian_char_fixes = {"€": "я",
                          "¬": "в"}
    URL_BASE_VERB = "https://cooljugator.com/ru/"
    URL_BASE_NOUN = "https://cooljugator.com/run/"
    URL_BASE_ADJECTIVE = "https://cooljugator.com/rua/"

    # WordType to class
    __WORD_TYPE_TYPES = {
        WordType.Verb: Verb,
        WordType.Noun: Noun,
        WordType.Adjective: Adjective,
    }

    def __init__(self):
        self.__404_words = set()
        self.__error_words = set()
        self.__lock = threading.Lock()
        self.BeautifulSoup = None

    def setup_imports(self):
        """Import the required python modules."""
        with self.__lock:
            from bs4 import BeautifulSoup
            self.BeautifulSoup = BeautifulSoup

    def download_word_info(self, word_type: WordType, name) -> Word:
        """
        Downloads info for a Word. Returns None on error.
        """
        key = (word_type, AccentedText(name).text.lower())
        with self.__lock:
            if key in self.__404_words:
                return None
            if key in self.__error_words:
                return None
        result = None
        if word_type in self.__WORD_TYPE_TYPES:
            Config.logger.info("Downloading {} info for: {} "
                                .format(key[0].name, key[1]))
            try:
                if word_type == WordType.Adjective:
                    result = self.download_adjective_info(name)
                elif word_type == WordType.Noun:
                    result = self.download_noun_info(name)
                elif word_type == WordType.Verb:
                    result = self.download_verb_info(name)
                else:
                    raise Exception(word_type)
            except Cooljugator404Exception:
                pass
            except Exception:
                Config.logger.error("Error downloading {} data for: {}"
                                .format(key[0].name, key[1]))
                with self.__lock:
                    self.__error_words.add(key)
                    traceback.print_exc()
        if result:
            result.set_complete(True)
            result.set_source(WordSourceEnum.Cooljugator)
            with self.__lock:
                if key in self.__error_words:
                    self.__error_words.remove(key)
        return result

    def download_noun_info(self, dictionary_form) -> Noun:
        """
        Download noun conjugation info.
        """
        dictionary_form = AccentedText(dictionary_form)
        key = (WordType.Noun, dictionary_form.text.lower())
        url = self.URL_BASE_NOUN + key[1]
        soup = self.__request_html(url, key=key)
        root = soup.body

        noun = Noun()
        noun.name = dictionary_form

        # Get singular forms
        noun.declension[(Plurality.Singular, Case.Nominative)] = self.__get_conjugation(root, ["nom_S_no_accent", "nom_no_accent"])
        noun.declension[(Plurality.Singular, Case.Genetive)] = self.__get_conjugation(root, ["gen_S_no_accent", "gen_no_accent"])
        noun.declension[(Plurality.Singular, Case.Dative)] = self.__get_conjugation(root, ["dat_S_no_accent", "dat_no_accent"])
        noun.declension[(Plurality.Singular, Case.Instrumental)] = self.__get_conjugation(root, ["instr_S_no_accent", "instr_no_accent"])
        noun.declension[(Plurality.Singular, Case.Prepositional)] = self.__get_conjugation(root, ["prep_S_no_accent", "prep_no_accent"])
        try:
            noun.declension[(Plurality.Singular, Case.Accusative)] = self.__get_conjugation(root, ["acc_S_no_accent", "acc_no_accent"])
        except:
            # Sometimes it doesn't list accusative for animate nouns, so assume genetive
            noun.declension[(Plurality.Singular, Case.Accusative)] = AccentedText(
                noun.declension[(Plurality.Singular, Case.Genetive)])

        # Get plural forms if present
        try:
            noun.declension[(Plurality.Plural, Case.Nominative)] = self.__get_conjugation(root, "nom_P")
            noun.declension[(Plurality.Plural, Case.Genetive)] = self.__get_conjugation(root, "gen_P")
            noun.declension[(Plurality.Plural, Case.Dative)] = self.__get_conjugation(root, "dat_P")
            noun.declension[(Plurality.Plural, Case.Instrumental)] = self.__get_conjugation(root, "instr_P")
            noun.declension[(Plurality.Plural, Case.Prepositional)] = self.__get_conjugation(root, "prep_P")
            try:
                noun.declension[(Plurality.Plural, Case.Accusative)] = self.__get_conjugation(root, "acc_P")
            except:
                # Sometimes it doesn't list accusative for animate nouns, so assume genetive
                noun.declension[(Plurality.Plural, Case.Accusative)] = AccentedText(
                    noun.declension[(Plurality.Plural, Case.Genetive)])
        except:
            pass

        gender = noun.classify_gender()
        if gender is not None:
            noun.gender = gender
            noun.indeclinable = False
        else:
            noun.gender = None
            noun.indeclinable = True
        return noun

    def download_adjective_info(self, dictionary_form) -> Adjective:
        """
        Download adjective conjugation info.
        """
        dictionary_form = AccentedText(dictionary_form)
        key = (WordType.Adjective, dictionary_form.text.lower())
        url = self.URL_BASE_ADJECTIVE+ key[1]
        soup = self.__request_html(url, key=key)
        root = soup.body

        adj = Adjective()
        adj.name = dictionary_form
        for gender, letter in ((Gender.Masculine, "M"),
                                (Gender.Femanine, "F"),
                                (Gender.Neuter, "N"),
                                (None, "P")):
            adj.declension[(gender, Case.Nominative)] = self.__get_conjugation(root, "nom_" + letter)
            adj.declension[(gender, Case.Accusative)] = self.__get_conjugation(root, "acc_anim_" + letter)
            adj.declension[(gender, Case.Genetive)] = self.__get_conjugation(root, "gen_" + letter)
            adj.declension[(gender, Case.Dative)] = self.__get_conjugation(root, "dat_" + letter)
            adj.declension[(gender, Case.Instrumental)] = self.__get_conjugation(root, "instr_" + letter)
            adj.declension[(gender, Case.Prepositional)] = self.__get_conjugation(root, "prep_" + letter)
        try:
            adj.short_form[gender] = self.__get_conjugation(root, "short_" + letter)
        except:
            adj.short_form[gender] = AccentedText("-")
        return adj

    def download_verb_info(self, infinitive) -> Verb:
        """
        Download verb conjugation info.
        """
        infinitive = AccentedText(infinitive)
        key = (WordType.Verb, infinitive.text.lower())
        url = self.URL_BASE_VERB + key[1]
        soup = self.__request_html(url, key=key)

        root = soup.body.find("div", attrs={"id": "conjugation-data"})
        top = root.find_all("div")[2]

        verb = Verb()
        verb.infinitive = infinitive
        verb.name = infinitive

        # Get the verb aspect
        non_past_tense = root.find("div", attrs={"class": "conjugation-cell conjugation-cell-four tense-title"}).text.lower()
        if "future" in non_past_tense:
            verb.aspect = Aspect.Perfective
            tense = "future"
        elif "present" in non_past_tense:
            verb.aspect = Aspect.Imperfective
            tense = "present"
        else:
            raise Execption(non_past_tense)

        # Parse the translation from the title
        title = root.find_all("h1")[0].text
        regex = re.compile(r".*?\[.*?\]\s+\((?P<translation>.*?)\).*")
        match = regex.search(title)
        verb.translation = AccentedText(match.group("translation"))

        # Parse the other meanings and aspect counterparts
        info = top.find("div", attrs={"id": "usage-info"}).text
        regex = re.compile(r"\s*(?P<info>.*?)\s*This verb.s .* counterparts?:\s*(?P<counterparts>.*)\.?\s*")
        match = regex.search(info)
        other_meanings = match.group("info")
        verb.info = AccentedText(other_meanings)
        counterparts = match.group("counterparts")
        verb.counterparts = [AccentedText(c.strip()) for c in counterparts.split(",") if bool(c.strip())]

        # Get conjugation info
        for index, (plurality, person) in enumerate(
            [(Plurality.Singular, Person.First),
                (Plurality.Singular, Person.Second),
                (Plurality.Singular, Person.Third), 
                (Plurality.Plural, Person.First), 
                (Plurality.Plural, Person.Second),
                (Plurality.Plural, Person.Third)]):
            verb.non_past[(plurality, person)] = self.__get_conjugation(
                root, [tense + str(index + 1), tense[0] + str(index + 1)], required=True)
        verb.past[(Plurality.Singular, Gender.Masculine)] = self.__get_conjugation(root, "past_singM", required=True)
        verb.past[(Plurality.Singular, Gender.Femanine)] = self.__get_conjugation(root, "past_singF", required=True)
        verb.past[(Plurality.Singular, Gender.Neuter)] = self.__get_conjugation(root, "past_singN", required=True)
        verb.past[(Plurality.Plural, None)] = self.__get_conjugation(root, "past_plur", required=True)
        verb.imperative[Plurality.Singular] = self.__get_conjugation(root, "imperative2")
        verb.imperative[Plurality.Plural] = self.__get_conjugation(root, "imperative5")
        verb.active_participles[Tense.Present] = self.__get_conjugation(root, "present_active_participle")
        verb.active_participles[Tense.Past] = self.__get_conjugation(root, "past_active_participle")
        verb.passive_participles[Tense.Present] = self.__get_conjugation(root, "present_passive_participle")
        verb.passive_participles[Tense.Past] = self.__get_conjugation(root, "past_passive_participle")
        verb.adverbial_participles[Tense.Present] = self.__get_conjugation(root, "present_adverbial_participle")
        verb.adverbial_participles[Tense.Past] = self.__get_conjugation(root, "past_adverbial_participle")
  
        # Parse the examples
        #verb.examples = []
        #example_table = soup.body.find("table", attrs={"id":
        #"example-sentences"})
        #for row in example_table.find("tbody").find_all("tr"):
        #  columns = row.find_all("td")
        #  russian = columns[0].text
        #  english = columns[1].text
        #  for a, b in russian_char_fixes.items():
        #    russian = russian.replace(a, b)
        #  verb.examples.append((russian, english))

        return verb
            
    def serialize(self) -> dict:
        """Serialize cooljugator data."""
        # Serialize list of words with download errors
        with self.__lock:
            word_404_data = {}
            for word_type, name in sorted(self.__404_words):
                if word_type.name not in word_404_data:
                    word_404_data[word_type.name] = []
                word_404_data[word_type.name].append(name)
                
            word_error_data = {}
            for word_type, name in sorted(self.__error_words):
                if word_type.name not in word_error_data:
                    word_error_data[word_type.name] = []
                word_error_data[word_type.name].append(name)

            data = {"error_words": word_error_data,
                    "404_words": word_404_data}
            return data
            
    def deserialize(self, data: dict):
        """Deserialize cooljugator data."""
        with self.__lock:
            self.__404_words = set()
            self.__error_words = set()
            if "404_words" in data:
                for word_type_name, word_list in data["404_words"].items():
                    word_type = getattr(WordType, word_type_name)
                    for name in word_list:
                        key = (word_type, name)
                        self.__404_words.add(key)
            if "error_words" in data:
                for word_type_name, word_list in data["error_words"].items():
                    word_type = getattr(WordType, word_type_name)
                    for name in word_list:
                        key = (word_type, name)
                        self.__error_words.add(key)
               
    def __get_conjugation(self, root, name, required=False):
        """
        Returns the conjugation text with the given element ID in
        the html document.
        """
        if not isinstance(name, list):
            name = [name]
            name.append(name[0] + "_no_accent")
        for n in name:
            element = root.find("div", attrs={"id": n})
            if element is not None:
                break
        if element is None:
            raise Exception("Cannot find element from ids: " + repr(name))
        if "data-stressed" in element.attrs:
            return AccentedText(element["data-stressed"])
        elif "data-default" in element.attrs:
            return AccentedText(element["data-default"])
        elif required:
            raise Exception(element.attrs)
        return AccentedText("")

    def __request_html(self, url: str, key: tuple):
        """
        Downloads an html page.
        """
        self.setup_imports()
        response = requests.get(url)
        soup = self.BeautifulSoup(response.text, features="lxml")
        # Check if this is a 404 error
        for h1 in soup.body.find_all("h1"):
            if "page not found" in h1.text.lower():
                with self.__lock:
                    self.__404_words.add(key)
                Config.logger.warning("404 Page not found: " + url)
                raise Cooljugator404Exception("404 Page not found: " + url)
        return soup
