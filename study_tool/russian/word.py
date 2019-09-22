import re
from study_tool.russian.types import *

CONSONANTS = "бвгджзклмнпрстфхцчшщй"
VOWELS = "аэыуояеёюи"
LETTERS = CONSONANTS + VOWELS + "ьъ"
ACCENT_CHAR = "´"
ACCENT_CHARS = "'´`"
HARD_VOWELS = "аоуыэ"
SOFT_VOWELS = "яёюие"
TO_SOFT = {"а": "я",
           "о": "ё",
           "у": "ю",
           "ы": "и",
           "э": "е"}

ACCENT_CHARS = "'’´`\u0301"  # \u0301 is special and rendered on prev char
STANDARD_ACCENT_CHAR = "'"

RUSSIAN_LETTERS_STRING = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

SPLIT_WORD_REGEX = re.compile("[{}]+".format(RUSSIAN_LETTERS_STRING))
RUSSIAN_LETTERS_REGEX = re.compile("[{}]".format(RUSSIAN_LETTERS_STRING))


class AccentedText:
    def __init__(self, text="", accents=None):
        if isinstance(text, AccentedText):
            self.text = text.text
            self.accents = tuple(text.accents)
        else:
            text = text
            length = 0
            if accents is None:
                self.accents = ()
                self.text = ""
                for index, c in enumerate(text):
                    x = ord(c)
                    if c in ACCENT_CHARS:
                        if length > 0:
                            self.accents += (length - 1,)
                    else:
                        self.text += c
                        length += 1
            else:
                self.text = text
                self.accents = tuple(accents)

    def __getitem__(self, index):
        return (self.text[index], index in self.accents)

    def __lt__(self, other):
        if isinstance(other, AccentedText):
            return self.text < other.text
        else:
            return self.text < str(other)

    def __add__(self, other):
        if isinstance(other, AccentedText):
            return AccentedText(self.text + other.text,
                self.accents + tuple(a + len(self.text) for a in other.accents))
        else:
            return AccentedText(self.text + str(other),
                self.accents)

    def __radd__(self, other):
        if isinstance(other, AccentedText):
            raise Exception(other)
        else:
            return AccentedText(str(other) + self.text,
                tuple(a + len(other) for a in self.accents))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        result = ""
        for c, accented in self:
            result += c
            if accented:
                result += STANDARD_ACCENT_CHAR
        return result

    def __eq__(self, other):
        return self.text == AccentedText(other).text

    def __ne__(self, other):
        return self.text != AccentedText(other).text


def has_russian_letters(text: AccentedText) -> bool:
    """Returns True if the given text has any russian letters in it."""
    return RUSSIAN_LETTERS_REGEX.search(text.text) is not None


def split_sentences(paragraph: str):
    return re.findall(r"\s*(.*?[\.\?\!]+)\s+", paragraph + " ")


def split_words(text: str):
    for match in SPLIT_WORD_REGEX.finditer(" " + text + " "):
        yield (match.group(0), match.start())


def get_word_text(word):
    word = word.lower()
    for c in ACCENT_CHARS:
        word = word.replace(c, "")
    return word


def get_stress_index(word):
    word = word.lower().strip()
    stress = None
    for c in ACCENT_CHARS:
        if c in word:
            stress = word.index(c) - 1
            break
    return stress


class Word:
    def __init__(self, custom=False):
        self.word_type = WordType.Noun
        self.name = AccentedText()
        self.meaning = None
        self.examples = []
        self.complete = False
        self.__forms = []
        self.__custom = custom

    def set_custom(self, custom: bool):
        self.__custom = custom

    def is_custom(self) -> bool:
        return self.__custom

    def is_complete(self) -> bool:
        return self.complete

    def get_key(self) -> tuple:
        return (self.word_type, self.name.text.lower().replace("ё", "е"))

    def get_name(self) -> AccentedText:
        return self.name

    def get_meaning(self):
        return self.meaning

    def get_all_forms(self) -> list:
        return [self.name] + self.__forms

    def serialize(self):
        data = {"type": self.word_type.name,
                "name": str(self.name),
                "examples": []}
        for russian, english in self.examples:
            data["examples"].append({
                "Russian": str(russian),
                "English": str(english)
            })
        data[self.word_type.name] = self.serialize()
        return data

    def deserialize(self, data):
        self.name = AccentedText(data["name"])
        self.word_type = getattr(WordType, data["type"])
        self.examples = []
        self.complete = True
        if "forms" in data:
            self.__forms = [AccentedText(x) for x in data["forms"]]
        if "examples" in data:
            for example in data["examples"]:
                self.examples.append((AccentedText(example["Russian"]),
                                      AccentedText(example["English"])))

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def __hash__(self):
        return hash((self.word_type, self.name.text))

    
class WordPatternToken:
    """
    Used for matching a single word.
    """
    def __init__(self, word=None):
        self.__regex = None
        self.__pattern = None
        self.__word_name = None
        if word:
            self.__word_name = word.lower()
        self.__word = None
        self.__forms = []

    def match(self, word: str):
        word = word.lower().replace("ё", "е")
        if self.__word:
            return word in self.__forms
        return self.__regex.match(word)

    def set_word(self, word: Word):
        self.__word = word
        self.__word_name = self.__word.get_name().text
        self.__forms = [x.text.lower().replace("ё", "е") for x in word.get_all_forms()]
        self.__pattern = None
        self.__regex = None

    def set_regex(self, pattern: str):
        self.__word = None
        self.__word_name = None
        self.__pattern = pattern
        pattern = re.sub("[ёе]", "[её]", pattern, flags=re.IGNORECASE)
        self.__regex = re.compile(
            "^" + pattern + "$", flags=re.IGNORECASE)
    
    def __repr__(self):
        if self.__word:
            return "[" + self.__word.get_name().text + "]"
        if self.__regex:
            return self.__pattern
        return "None"


class WordPattern:
    """
    Used for matching words
    """
    def __init__(self, pattern=None):
        self.__pattern = pattern
        if pattern is None:
            self.__tokens = []
        elif isinstance(pattern, list):
            self.__tokens = [WordPatternToken(x) for x in pattern]
        elif isinstance(pattern, str):
            self.__tokens = [WordPatternToken(x) for x in pattern.split()]
        else:
            raise TypeError(pattern)

    def add_regex(self, pattern: str):
        token = WordPatternToken()
        token.set_regex(pattern)
        self.__tokens.append(token)

    def add_word(self, word: Word):
        token = WordPatternToken()
        token.set_word(word)
        self.__tokens.append(token)

    def match(self, text: str) -> bool:
        return self.search(text) is not None

    def search(self, text: str):
        word_list = list(split_words(text))
        start = 0
        while start < len(word_list) - len(self.__tokens) + 1:
            matches = True
            for index, token in enumerate(self.__tokens):
                word, _ = word_list[start + index]
                word = word.lower()
                if not token.match(word):
                    matches = False
                    break
            start += 1
            if matches:
                return start
        return None

    def finditer(self, text: str):
        word_list = list(split_words(text))
        start = 0
        while start < len(word_list) - len(self.__tokens) + 1:
            matches = True
            instances = []
            for index, token in enumerate(self.__tokens):
                word, word_start = word_list[start + index]
                if not token.match(word):
                    matches = False
                    break
                instances.append((word_start, word))
            start += 1
            if matches:
                for instance in instances:
                    yield instance

    def __getitem__(self, index: int):
        return self.__tokens[index]

    def __iter__(self):
        for token in self.__tokens:
            yield token

    def __repr__(self):
        return "WordPattern(" + ", ".join(repr(x) for x in self.__tokens) + ")"