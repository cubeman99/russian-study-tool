import json
import shutil
import random
import re
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.adjective import Adjective
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.card import *
from study_tool.card_attributes import *
from study_tool.config import Config
from study_tool.external import ponyfiction
from study_tool.russian.story import Story, Chapter

SPLIT_WORD_REGEX = re.compile(
    r"[абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ]+")


def split_sentences(paragraph: str):
    return re.findall(r"\s*(.*?[\.\?\!]+)\s+", paragraph + " ")


def get_word_occurances(word, text):
    sentence = text
    text = word
    if not isinstance(text, list):
        text_list0 = [text]
    else:
        text_list0 = list(text)

    text_list = []
    for text in text_list0:
        if isinstance(text, AccentedText):
            text = text.text
        text = text.lower().replace("...", "").strip()
        if any(letter in text for letter in LETTERS):
            text_list.append(text)
    whole_word = True
    if len(text_list) == 1 and " " in text_list[0]:
        whole_word = False

    instances = []
    found = False
    if whole_word:
        for word, start in split_words(sentence):
            if word.lower() in text_list:
                found = True
                instances.append((start, word))
                break
    else:
        for text in text_list:
            if text in sentence.lower():
                found = True
                break
    if found:
        return instances


class ExampleDatabase:
    def __init__(self):
        self.stories = []

    def get_example_sentences(self, text, count=None):
        examples = list(self.iter_example_sentences(text))
        random.shuffle(examples)
        if count is not None:
            return examples[:count]
        return examples

    def iter_example_sentences(self, text):
        if not isinstance(text, list):
            text_list0 = [text]
        else:
            text_list0 = list(text)

        text_list = []
        for text in text_list0:
            if isinstance(text, AccentedText):
                text = text.text
            text = text.lower().replace("...", "").strip()
            if any(letter in text for letter in LETTERS):
                text_list.append(text)
                if "ё" in text:
                    text_list.append(text.replace("ё", "е"))
        whole_word = True
        if len(text_list) == 1 and " " in text_list[0]:
            whole_word = False

        for story in self.stories:
            for chapter in story.chapters:
                for paragraph in chapter.paragraphs:
                    paragraph = paragraph.text
                    for sentence in split_sentences(paragraph):
                        instances = []
                        found = False
                        if whole_word:
                            for word, start in split_words(sentence):
                                if word.lower() in text_list:
                                    found = True
                                    instances.append((start, word))
                                    break
                        else:
                            for text in text_list:
                                if text in sentence.lower():
                                    found = True
                                    break
                        if found:
                            yield sentence, instances

    def download_ponyfiction_story(self, story_id: int):
        Config.logger.info("Downloading ponyfiction story {}".format(story_id))
        story = ponyfiction.download_story(story_id)
        if story is not None:
            Config.logger.info("Downloaded ponyfiction story '{}' with {} chapters!"
                               .format(story.title, len(story.chapters)))
            self.stories.append(story)
        return story

    def save(self, path: str):
        data = self.serialize()
        with open(path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)

    def load(self, path: str):
        with open(path, "r", encoding="utf8") as f:
            data = json.load(f)
        self.deserialize(data)

    def serialize(self):
        state = {"stories": [story.serialize() for story in self.stories]}
        return state

    def deserialize(self, state):
        self.stories = []
        for story_state in state["stories"]:
            story = Story()
            story.deserialize(story_state)
            self.stories.append(story)

    def load_story_text_file(self, path: str):
        story = Story()
        chapter = None
        english = False

        with open(path, "r", encoding="utf8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("@"):
                    tokens = line.split()
                    command = tokens[0][1:].lower()
                    parameters = tokens[1:]
                    if command == "title":
                        story.title = AccentedText(" ".join(parameters))
                        english = False
                    elif command == "url":
                        story.url = parameters[0]
                    elif command == "chapter":
                        chapter = Chapter()
                        chapter.number = int(parameters[0])
                        chapter.title = AccentedText(" ".join(parameters[1:]))
                        story.chapters.append(chapter)
                        english = False
                    elif command == "english":
                        english = True
                    else:
                        raise KeyError(command)
                elif len(line) > 0:
                    if chapter is None:
                        chapter = Chapter()
                        chapter.number = 1
                        chapter.title = AccentedText(story.title)
                        story.chapters.append(chapter)
                    if not english:
                        chapter.paragraphs.append(AccentedText(line))

        if len(story.chapters) == 0:
            raise Exception("No chapters")
        self.stories.append(story)
        return story
