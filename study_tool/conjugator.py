import requests
from lxml import etree
from bs4 import BeautifulSoup
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.word_database import Verb
import re

russian_char_fixes = {"€": "я",
                      "¬": "в"}


def get_conjugation(root, name, required=False):
  element = root.find("div", attrs={"id": name})
  if "data-stressed" in element.attrs:
    return AccentedText(element["data-stressed"])
  elif "data-default" in element.attrs:
    return AccentedText(element["data-default"])
  elif required:
    raise Exception(element.attrs)
  else:
    return AccentedText("")

def main():
  get_verb_info("спрашивать")
  get_verb_info("Спросить")

def request_html(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, features="lxml")
  return soup

def get_verb_info(infinitive):
  infinitive = AccentedText(infinitive)
  url = "https://cooljugator.com/ru/" + AccentedText(infinitive).text.lower()
  soup = request_html(url)

  #with open("test.html", "r", encoding="utf8") as f:
  #  soup = BeautifulSoup(f)
  
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
  verb.counterparts = [AccentedText(c.strip()) for c in counterparts.split(",")]

  verb.non_past[(Plurality.Singular, Person.First)] = get_conjugation(root, tense + "1", required=True)
  verb.non_past[(Plurality.Singular, Person.Second)] = get_conjugation(root, tense + "2", required=True)
  verb.non_past[(Plurality.Singular, Person.Third)] = get_conjugation(root, tense + "3", required=True)
  verb.non_past[(Plurality.Plural, Person.First)] = get_conjugation(root, tense + "4", required=True)
  verb.non_past[(Plurality.Plural, Person.Second)] = get_conjugation(root, tense + "5", required=True)
  verb.non_past[(Plurality.Plural, Person.Third)] = get_conjugation(root, tense + "6", required=True)
  verb.past[(Plurality.Singular, Gender.Masculine)] = get_conjugation(root, "past_singM", required=True)
  verb.past[(Plurality.Singular, Gender.Femanine)] = get_conjugation(root, "past_singF", required=True)
  verb.past[(Plurality.Singular, Gender.Neuter)] = get_conjugation(root, "past_singN", required=True)
  verb.past[(Plurality.Plural, None)] = get_conjugation(root, "past_plur", required=True)
  verb.imperative[Plurality.Singular] = get_conjugation(root, "imperative2")
  verb.imperative[Plurality.Plural] = get_conjugation(root, "imperative5")
  verb.active_participles[Tense.Present] = get_conjugation(root, "present_active_participle")
  verb.active_participles[Tense.Past] = get_conjugation(root, "past_active_participle")
  verb.passive_participles[Tense.Present] = get_conjugation(root, "present_passive_participle")
  verb.passive_participles[Tense.Past] = get_conjugation(root, "past_passive_participle")
  verb.adverbial_participles[Tense.Present] = get_conjugation(root, "present_adverbial_participle")
  verb.adverbial_participles[Tense.Past] = get_conjugation(root, "past_adverbial_participle")
  
  # Parse the examples   
  #verb.examples = []
  #example_table = soup.body.find("table", attrs={"id": "example-sentences"})
  #for row in example_table.find("tbody").find_all("tr"):
  #  columns = row.find_all("td")
  #  russian = columns[0].text
  #  english = columns[1].text
  #  for a, b in russian_char_fixes.items():
  #    russian = russian.replace(a, b)
  #  verb.examples.append((russian, english))

  return verb
