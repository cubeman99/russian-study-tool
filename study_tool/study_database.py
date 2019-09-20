import os
import threading
import time
import yaml
from datetime import datetime
from cmg.event import Event
from cmg.utilities.read_write_lock import ReadWriteLock
from study_tool.card import Card
from study_tool.card_attributes import CardAttributes
from study_tool.config import Config
from study_tool.russian.types import WordType
from study_tool.russian.types import parse_word_type


def calc_history_score(history):
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


class CardGroupMetrics:
    def __init__(self):
        self.history_score = 0.0
        self.proficiency_counts = []
        for level in range(0, Config.proficiency_levels + 1):
            self.proficiency_counts.append(0)

    def get_total_count(self):
        return sum(self.proficiency_counts)

    def get_proficiency_percent(self):
        score = 0
        potential_score = 0
        for level, count in enumerate(self.proficiency_counts):
            score += count * Config.proficiency_level_score_multiplier[level]
            potential_score += count
        return score / potential_score

    def get_proficiency_count(self):
        return self.get_proficiency_percent() * self.get_total_count()

    def serialize(self):
        return {"history_score": self.history_score,
                "proficiency_counts": self.proficiency_counts}

    def deserialize(self, state):
        self.history_score = state["history_score"]
        self.proficiency_counts = list(state["proficiency_counts"])

    def copy(self, other):
        self.history_score = other.history_score
        self.proficiency_counts = list(other.proficiency_counts)



class StudyMetrics:
    def __init__(self, date=None):
        self.date = date if date is not None else datetime.now()
        self.all_metrics = CardGroupMetrics()
        self.word_type_metrics = {}
        for word_type in WordType:
            self.word_type_metrics[word_type] = CardGroupMetrics()

    def get_date_string(self) -> str:
        return self.date.strftime("%Y/%m/%d")

    def serialize(self):
        state = {"all": self.all_metrics.serialize()}
        for word_type, metrics in self.word_type_metrics.items():
            if metrics.get_total_count() > 0:
                state[word_type.name] = metrics.serialize()
        return state

    def deserialize(self, state):
        self.all_metrics.deserialize(state["all"])
        for word_type in WordType:
            if word_type.name in state:
                self.word_type_metrics[word_type].deserialize(state[word_type.name])

    def copy(self, other):
        self.all_metrics.copy(other.all_metrics)
        for word_type in WordType:
            self.word_type_metrics[word_type].copy(other.word_type_metrics[word_type])

                

class CardStudyData:

    def __init__(self):
        self.proficiency_level = 0  # 0 = new/unseen
        self.history = []  # History of True or False markings
        self.last_encounter_time = None

    def is_encountered(self) -> bool:
        return self.last_encounter_time is not None

    def get_proficiency_level(self) -> int:
        return self.proficiency_level

    def get_last_encounter_time(self) -> float:
        return self.last_encounter_time
        
    def get_proficiency_score(self) -> float:
        """Get the card's proficiency score."""
        return max(0.0, float(self.proficiency_level - 1) /
                   (Config.proficiency_levels - 1))

    def get_history_list(self) -> list:
        """Get the card's history list."""
        return self.history

    def get_history_score(self) -> float:
        """Get the card's current history score."""
        return calc_history_score(self.history)

    def get_next_history_score(self, knew_it: bool) -> float:
        """Get the card's next history score, given whether it was known or not."""
        history = [knew_it] + self.history
        return calc_history_score(history[:Config.max_card_history_size])
    
    def elapsed_time_string(self) -> str:
        """
        Get the string representing the time since the last encouder.
        example: "15 minutes ago".
        """
        elapsed_time = time.time() - self.last_encounter_time
        units = "second"
        if elapsed_time > 60:
            units = "minute"
            elapsed_time /= 60
            if elapsed_time > 60:
                units = "hour"
                elapsed_time /= 60
                if elapsed_time > 24:
                    units = "day"
                    elapsed_time /= 24
        elapsed_time = int(round(elapsed_time))
        return "{} {}{} ago".format(elapsed_time, units,
                                    "s" if elapsed_time != 1 else "")

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
    """
    Database class to store study data for Cards, and overall study metrics
    """

    def __init__(self, card_database):
        """
        Creates an empty database.
        """
        self.__word_data_path = None
        self.__card_database = card_database
        self.__metrics_history = {}
        self.__study_data_dict = {}
        self.__lock = ReadWriteLock()

        # Dirty state
        self.__lock_dirty = threading.RLock()
        self.__dirty = False

        # Events
        self.card_study_data_changed = Event(Card, CardStudyData)

        # Connect
        self.__card_database.card_key_changed.connect(self.__on_card_key_changed)

    def is_data_modified(self) -> bool:
        """Returns True if the data has been modified since the last load/save."""
        return self.__dirty

    def get_card_study_data(self, card: Card) -> CardStudyData:
        """Get or create the study data for a card."""
        with self.__lock.acquire_read():
            if card in self.__study_data_dict:
                return self.__study_data_dict[card]
        return self.create_card_study_data(card)
    
    def get_study_metrics(self) -> StudyMetrics:
        """Get study metrics for all cards."""
        metrics = StudyMetrics()
        with self.__lock.acquire_read():
            for card, data in self.__study_data_dict.items():
                history_score = data.get_history_score()
                word_type = card.get_word_type()
                m = metrics.word_type_metrics[word_type]
                m.proficiency_counts[data.get_proficiency_level()] += 1
                m.history_score += history_score
                metrics.all_metrics.proficiency_counts[data.get_proficiency_level()] += 1
                metrics.all_metrics.history_score += history_score
        return metrics

    def get_group_study_metrics(self, study_set):
        metrics = CardGroupMetrics()
        for card in study_set.cards:
            study_data = self.get_card_study_data(card)
            metrics.history_score += study_data.get_history_score()
            metrics.proficiency_counts[study_data.get_proficiency_level()] += 1
        return metrics

    def mark_card(self, card: Card, knew_it: bool):
        """
        Mark a card as "knew it" or "didn't know it". This will adjust its
        proficiencly level accordingly.
        """
        with self.__lock.acquire_write():
            study_data = self.get_card_study_data(card)
            study_data.last_encounter_time = time.time()
            study_data.history.insert(0, knew_it)
            if len(study_data.history) > Config.max_card_history_size:
                study_data.history = study_data.history[:Config.max_card_history_size]
        
            # Update proficiencly level
            if study_data.proficiency_level == 0:
                study_data.proficiency_level = 3 if knew_it else 1
            elif knew_it:
                study_data.proficiency_level = min(
                    study_data.proficiency_level + 1, Config.proficiency_levels)
            else:
                study_data.proficiency_level = max(
                    1, study_data.proficiency_level - 1)
            with self.__lock_dirty:
                self.__dirty = True

        self.card_study_data_changed.emit(card, study_data)

    def create_card_study_data(self, card: Card) -> CardStudyData:
        """Create study data for a card."""
        study_data = CardStudyData()
        with self.__lock.acquire_write():
            assert card not in self.__study_data_dict
            self.__study_data_dict[card] = study_data
            card.set_study_data(study_data)
            return study_data

    def clear(self):
        """Clears all study data."""
        with self.__lock.acquire_write():
            self.__metrics_history = {}
            self.__study_data_dict = {}

    def save_all_changes(self):
        """Saves all modified data to file."""
        with self.__lock_dirty:
            if self.__dirty:
                self.save()
    
    def save(self, path=None):
        """Save the study data to file."""
        with self.__lock.acquire_read():
            if path is None:
                path = self.__word_data_path
            self.__word_data_path = path
            assert path is not None

            Config.logger.debug("Saving study data to: " + path)
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
                
                opened_file.write(b"cards:\n")
                for card_state in cards_state:
                    opened_file.write(b"  - ")
                    yaml.dump(
                        card_state, opened_file, encoding="utf8",
                        allow_unicode=True, default_flow_style=True,
                        Dumper=yaml.CDumper)

                opened_file.write(b"metrics:\n")
                metrics_state_dict = list(metrics_state_dict.items())
                metrics_state_dict.sort(key=lambda x: x[0])
                for data_string, metrics_state in metrics_state_dict:
                    opened_file.write("  {}: ".format(data_string).encode())
                    yaml.dump(
                        metrics_state, opened_file, encoding="utf8",
                        allow_unicode=True, default_flow_style=True,
                        Dumper=yaml.CDumper)

            if os.path.isfile(path):
                os.remove(path)
            os.rename(temp_path, path)
            with self.__lock_dirty:
                self.__dirty = False

    def load(self, path: str, card_database):
        """Load the study data from file."""
        with self.__lock.acquire_write():
            self.__word_data_path = path
            Config.logger.info("Loading study data from: " + path)
            with open(path, "r", encoding="utf8") as f:
                state = yaml.load(f, Loader=yaml.CLoader)
                Config.logger.info("Deserializing study data from: " + path)
                self.__deserialize(state, card_database)
            with self.__lock_dirty:
                self.__dirty = False
                
    def __update_current_metrics(self):
        current_metrics = self.get_study_metrics()
        self.__metrics_history[current_metrics.get_date_string()] = current_metrics

    def __on_card_key_changed(self, *args, **kwargs):
        """Called after a card's key changes."""
        with self.__lock_dirty:
            self.__dirty = True

    def __serialize(self) -> dict:
        """Serialize the study data into a dictionary."""
        self.__update_current_metrics()

        # Save metrics history
        state = {"save_time": time.time(), 
                 "cards": [],
                 "metrics": {}}
        for date_string, metrics in self.__metrics_history.items():
            state["metrics"][date_string] = metrics.serialize()

        # Serialize card study data
        items = list(self.__study_data_dict.items())
        items.sort(key=lambda item: item[0].get_key())
        for card, card_study_data in items:
            key = card.get_key()
            card_state = [key[0].name.lower(), key[1], key[2]]
            card_state += card_study_data.serialize()
            state["cards"].append(card_state)
        return state

    def __deserialize(self, state: dict, card_database):
        """Deserialize the study data from a dictionary."""

        # Deserialize metrics hisstory
        self.__metrics_history = {}
        for date_string, metrics_state in state["metrics"].items():
            date = datetime.strptime(date_string, "%Y/%m/%d")
            metrics = StudyMetrics(date=date)
            metrics.deserialize(metrics_state)
            self.__metrics_history[metrics.get_date_string()] = metrics

        # Deserialize card study data
        self.__study_data_dict = {}
        for card_state in state["cards"]:
            word_type = parse_word_type(card_state[0])
            key = (word_type, card_state[1], card_state[2])
            card = self.__card_database.get_card_by_key(*key)
            if card is None:
                Config.logger.error("Study data: Error finding card with key: " + str(key))
                continue
            card_study_data = CardStudyData()
            card_study_data.deserialize(card_state[3:])
            self.__study_data_dict[card] = card_study_data
            card.set_study_data(card_study_data)

