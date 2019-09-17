import os
import random
import re
import threading
import time
import yaml
from datetime import datetime
from study_tool.card import Card, CardSide, SourceLocation
from study_tool.card_set import CardSet, CardSetPackage, CardGroupMetrics, StudySet
from study_tool.card_attributes import CardAttributes
from study_tool.external import googledocs
from study_tool.russian.types import *
from study_tool.russian.types import parse_word_type
from study_tool.russian.word import *
from study_tool.config import Config
from study_tool.word_database import WordDatabase

TOKEN_DELIMETERS = ["--", "–", "-"]
WORD_TYPE_DICT = {"none": WordType.Other,
                  None: WordType.Other}
for word_type in WordType:
    WORD_TYPE_DICT[word_type.name.lower()] = word_type
    

def get_history_score(history):
    """
    Calculate the history score given a list of pass/fail booleans.
    Lower indices represent the most recent entries.
    """
    if len(history) == 0:
        return 0.0
    score = 1.0
    for index, good in enumerate(history):
        if not good:
            score -= 0.5 / (index + 2)
    min_length = 6
    if len(history) < min_length:
        score /= (min_length - len(history) + 1.0)
    return score


class StudyMetrics:
    def __init__(self):
        self.date = datetime.now()
        self.all_metrics = CardGroupMetrics()
        self.word_type_metrics = {}
        for word_type in WordType:
            self.word_type_metrics[word_type] = CardGroupMetrics()

    def get_date_string(self) -> str:
        return self.date.strftime("%Y/%m/%d")

    def serialize(self):
        state = {"date": self.get_date_string(),
                 "all_metrics": self.all_metrics.serialize(),
                 "card_type_metrics": {}}
        for word_type, metrics in self.word_type_metrics.items():
            if metrics.get_total_count() > 0:
                state["card_type_metrics"][word_type.name] = metrics.serialize()
        return state

    def deserialize(self, state):
        self.date = datetime.strptime(state["date"], "%Y/%m/%d")
        self.all_metrics.deserialize(state["all_metrics"])
        for word_type in WordType:
            if word_type.name in state["card_type_metrics"]:
                self.word_type_metrics[word_type].deserialize(
                    state["card_type_metrics"][word_type.name])

                

class CardStudyData:

    def __init__(self):
        self.proficiency_level = 0  # 0 = new/unseen
        self.history = []  # History of True or False markings
        self.last_encounter_time = None

    def get_proficiency_level(self) -> int:
        return self.proficiency_level

    def get_last_encounter_time(self) -> float:
        return self.last_encounter_time
        
    def get_proficiency_score(self) -> float:
        """Get the key proficiency score."""
        return max(0.0, float(self.proficiency_level - 1) /
                   (Config.proficiency_levels - 1))

    def get_history_score(self) -> float:
        """Get the card's current history score."""
        return get_history_score(self.history)

    def get_next_history_score(self, knew_it: bool) -> float:
        """Get the card's next history score, given whether it was known or not."""
        history = [knew_it] + self.history
        return get_history_score(history[:Config.max_card_history_size])

    def serialize(self):
        """Serialize the study data."""
        history_str = "".join("T" if h else "F" for h in self.history)
        return [self.proficiency_level, self.last_encounter_time, history_str]

    def deserialize(self, state):
        """Deserialize the study data."""
        self.proficiency_level = state[0]
        self.last_encounter_time = state[1]
        history_str = state[2]
        self.history = [c == "T" for c in history_str]


class StudyDatabase:

    def __init__(self):
        self.__metrics_history = {}
        self.__study_data_dict = {}
        self.__lock = threading.RLock()

    def get_card_study_data(self, card: Card) -> CardStudyData:
        key = card.get_key()
        with self.__lock:
            if key in self.__study_data_dict:
                return self.__study_data_dict[key]
            return self.create_card_study_data(card)
    
    def get_study_metrics(self) -> StudyMetrics:
        """Get study metrics for all cards."""
        metrics = StudyMetrics()
        metrics.all_metrics = self.get_group_metrics(
            self.__study_data_dict.values())
        for word_type in WordType:
            metrics.word_type_metrics[word_type] = self.get_group_metrics(
                (data for key, data in self.__study_data_dict.items() if key[0] == word_type))
        return metrics

    def get_group_metrics(self, card_study_data_list: list) -> CardGroupMetrics:
        """Get study metrics for a group of cards."""
        metrics = CardGroupMetrics()
        for key, data in self.__study_data_dict.items():
            metrics.proficiency_counts[data.get_proficiency_level()] += 1
            metrics.history_score += data.get_history_score()
        return metrics

    def create_card_study_data(self, card: Card) -> CardStudyData:
        key = card.get_key()
        study_data = CardStudyData()
        with self.__lock:
            assert key not in self.__study_data_dict
            self.__study_data_dict[key] = study_data
            return study_data

    def clear(self):
        """Clears all study data."""
        with self.__lock:
            self.__metrics_history = {}
            self.__study_data_dict = {}
    
    def save(self, path: str):
        """Save the study data to file."""
        Config.logger.debug("Saving study data to: " + path)
        with self.__lock:
            state = self.__serialize()
            cards_state = state["cards"]
            del state["cards"]
            metrics_state_dict = state["metrics"]
            del state["metrics"]
            temp_path = path + ".temp"
            with open(temp_path, "wb") as opened_file:
                yaml.dump(state, opened_file, encoding="utf8",
                          allow_unicode=True, default_flow_style=False,
                          Dumper=yaml.CDumper)
                opened_file.write(b"  metrics:\n")
                metrics_state_dict = list(metrics_state_dict.items())
                metrics_state_dict.sort(key=lambda x: x[0])
                for data_string, metrics_state in metrics_state_dict:
                    opened_file.write("    {}: ".format(data_string).encode())
                    yaml.dump(
                        metrics_state, opened_file, encoding="utf8",
                        allow_unicode=True, default_flow_style=True,
                        Dumper=yaml.CDumper)
                opened_file.write(b"  cards:\n")
                for card_state in cards_state:
                    opened_file.write(b"    - ")
                    yaml.dump(
                        card_state, opened_file, encoding="utf8",
                        allow_unicode=True, default_flow_style=True,
                        Dumper=yaml.CDumper)

            if os.path.isfile(path):
                os.remove(path)
            os.rename(temp_path, path)

    def load(self, path: str):
        """Load the study data from file."""
        with self.__lock:
            Config.logger.info("Loading study data from: " + path)
            with open(path, "r", encoding="utf8") as f:
                state = yaml.load(f, Loader=yaml.CLoader)
                Config.logger.info("Deserializing study data from: " + path)
                self.__deserialize(state)

    def __serialize(self) -> dict:
        """Serialize the study data into a dictionary."""
        Config.logger.info("Serializing study data")

        # Save metrics history
        state = {"save_time": time.time(), 
                 "cards": [],
                 "metrics": {}}
        current_metrics = self.get_study_metrics()
        self.__metrics_history[current_metrics.get_date_string()] = current_metrics
        for date_string, metrics in self.__metrics_history.items():
            state["metrics"][date_string] = metrics.serialize()

        # Serialize card study data
        items = list(self.__study_data_dict.items())
        items.sort(key=lambda x: x[0])
        for key, card_study_data in items:
            card_state = [key[0].name.lower(), key[1], key[2]]
            card_state += card_study_data.serialize()
            state["cards"].append(card_state)
        return state

    def __deserialize(self, state: dict):
        """Deserialize the study data from a dictionary."""
        Config.logger.info("Deserializing study data")
        
        # Deserialize metrics hisstory
        self.__metrics_history = {}
        for metrics_state in state["metrics"]:
            metrics = StudyMetrics()
            metrics.deserialize(metrics_state)
            self.__metrics_history[metrics.get_date_string()] = metrics
        current_metrics = self.get_study_metrics()
        self.__metrics_history[current_metrics.get_date_string()] = current_metrics

        # Deserialize card study data
        for card_state in state["cards"]:
            word_type = parse_word_type(card_state[0])
            key = (word_type, card_state[1], card_state[2])
            card_study_data = CardStudyData()
            card_study_data.deserialize(card_state[3:])
            self.__study_data_dict[key] = card_study_data
