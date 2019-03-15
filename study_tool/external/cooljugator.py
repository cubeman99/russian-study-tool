import requests
import traceback
import re
from bs4 import BeautifulSoup
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.russian.noun import Noun
from study_tool.russian.verb import Verb
from study_tool.russian.adjective import Adjective
from study_tool.config import Config

russian_char_fixes = {"€": "я",
                      "¬": "в"}


def get_conjugation(root, name, required=False):
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
  else:
    return AccentedText("")

def request_html(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, features="lxml")

  # Check if this is a 404 error
  for h1 in soup.body.find_all("h1"):
    if "page not found" in h1.text.lower():
      Config.logger.warning("404 Page not found: " + url)
      raise Exception("404 Page not found: " + url)

  return soup


def get_noun_info(dictionary_form):
  try:
    dictionary_form = AccentedText(dictionary_form)
    url = "https://cooljugator.com/run/" + AccentedText(dictionary_form).text.lower()
    soup = request_html(url)
    root = soup.body

    noun = Noun()
    noun.name = dictionary_form
    noun.declension[(Plurality.Singular, Case.Nominative)] = get_conjugation(root, "nom_S")
    noun.declension[(Plurality.Singular, Case.Accusative)] = get_conjugation(root, "acc_S")
    noun.declension[(Plurality.Singular, Case.Genetive)] = get_conjugation(root, "gen_S")
    noun.declension[(Plurality.Singular, Case.Dative)] = get_conjugation(root, "dat_S")
    noun.declension[(Plurality.Singular, Case.Instrumental)] = get_conjugation(root, "instr_S")
    noun.declension[(Plurality.Singular, Case.Prepositional)] = get_conjugation(root, "prep_S")
    noun.declension[(Plurality.Plural, Case.Nominative)] = get_conjugation(root, "nom_P")
    noun.declension[(Plurality.Plural, Case.Accusative)] = get_conjugation(root, "acc_P")
    noun.declension[(Plurality.Plural, Case.Genetive)] = get_conjugation(root, "gen_P")
    noun.declension[(Plurality.Plural, Case.Dative)] = get_conjugation(root, "dat_P")
    noun.declension[(Plurality.Plural, Case.Instrumental)] = get_conjugation(root, "instr_P")
    noun.declension[(Plurality.Plural, Case.Prepositional)] = get_conjugation(root, "prep_P")
    gender = noun.classify_gender()
    if gender is not None:
      noun.gender = gender
      noun.indeclinable = False
    else:
      noun.gender = None
      noun.indeclinable = True
    noun.complete = True
    return noun
  except:
    Config.logger.error("Error downloading noun data for: " + dictionary_form.text)
    traceback.print_exc()


def get_adjective_info(dictionary_form):
  try:
    dictionary_form = AccentedText(dictionary_form)
    url = "https://cooljugator.com/rua/" + AccentedText(dictionary_form).text.lower()
    soup = request_html(url)
    root = soup.body

    adj = Adjective()
    adj.name = dictionary_form
    for gender, letter in ((Gender.Masculine, "M"),
                           (Gender.Femanine, "F"),
                           (Gender.Neuter, "N"),
                           (None, "P")):
      adj.declension[(gender, Case.Nominative)] = get_conjugation(root, "nom_" + letter)
      adj.declension[(gender, Case.Accusative)] = get_conjugation(root, "acc_anim_" + letter)
      adj.declension[(gender, Case.Genetive)] = get_conjugation(root, "gen_" + letter)
      adj.declension[(gender, Case.Dative)] = get_conjugation(root, "dat_" + letter)
      adj.declension[(gender, Case.Instrumental)] = get_conjugation(root, "instr_" + letter)
      adj.declension[(gender, Case.Prepositional)] = get_conjugation(root, "prep_" + letter)
      try:
        adj.short_form[gender] = get_conjugation(root, "short_" + letter)
      except:
        adj.short_form[gender] = AccentedText("-")
    adj.complete = True
    return adj
  except:
    Config.logger.error("Error downloading adjective data for: " + dictionary_form.text)
    traceback.print_exc()


def get_verb_info(infinitive):
  try:
    infinitive = AccentedText(infinitive)
    url = "https://cooljugator.com/ru/" + AccentedText(infinitive).text.lower()
    soup = request_html(url)

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
    for index, (plurality, person) in enumerate([
      (Plurality.Singular, Person.First),
      (Plurality.Singular, Person.Second),
      (Plurality.Singular, Person.Third), 
      (Plurality.Plural, Person.First), 
      (Plurality.Plural, Person.Second),
      (Plurality.Plural, Person.Third)]):
      verb.non_past[(plurality, person)] = get_conjugation(
        root, [tense + str(index + 1), tense[0] + str(index + 1)], required=True)
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

    verb.complete = True
    return verb
  except:
    Config.logger.error("Error downloading verb data for: " + infinitive.text)
    traceback.print_exc()

