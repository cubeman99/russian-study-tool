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
            return AccentedText(
                self.text + other.text,
                self.accents + tuple(a + len(self.text) for a in other.accents))
        else:
            return AccentedText(
                self.text + str(other),
                self.accents)

    def __radd__(self, other):
        if isinstance(other, AccentedText):
            raise Exception(other)
        else:
            return AccentedText(
                str(other) + self.text,
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

    def get_key(self) -> tuple:
        return (self.word_type, self.name.text.lower().replace("ё", "е"))

    def get_name(self) -> AccentedText:
        return self.name

    def get_meaning(self):
        return self.meaning

    def get_all_forms(self):
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
