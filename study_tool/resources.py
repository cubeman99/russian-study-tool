import json
import os
import shutil
import threading
import yaml
from cmg.event import Event
from cmg.utilities import ReadWriteLock
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




class Res:

    class Images:
        icon_cooljugator = "images/icons/cooljugator.jpg"
        icon_audio = "images/icons/audio.png"
        icon_wiktionary = "images/icons/wiktionary.png"


