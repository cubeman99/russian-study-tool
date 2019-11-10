import requests
import traceback
import re
from bs4 import BeautifulSoup, NavigableString
from study_tool.config import Config
from study_tool.russian.word import AccentedText, has_russian_letters
from study_tool.russian.verb import Verb
from study_tool.russian.noun import Noun
from study_tool.russian.adjective import Adjective
from study_tool.russian.types import WordType, Plurality, Case, Person, Aspect, Gender, Participle, Tense
from study_tool.russian import types
from study_tool.russian.story import Story, Chapter
import yaml

def request_html(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, features="lxml")
  return soup

def is_section(tag, h, name):
    if not tag.parent.name != h:
        return False
    return (tag.text.strip().lower() == "russian")

def get_section(root, h, name):
    section = root.find(lambda tag: is_section(tag, h, name))
    print("section {} '{}' = {}".format(h, name, repr(section)))
    return section

class WiktionaryData:
    """
    Data representing a single page on Wiktionary for a term.
    """
    def __init__(self, name: AccentedText):
        self.name = AccentedText(name)
        self.etymology = AccentedText()
        self.pronunciation = AccentedText()
        self.words = {}
        self.related_terms = []
        self.audio_sources = {}

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "name": self.name.raw,
            "etymology": self.etymology.raw,
            "words": {},
        }
        if self.audio_sources:
            data["audo_sources"] = {}
            for extension, url in self.audio_sources.items():
                data["audo_sources"][extension] = url
        for word_type, word_data in self.words.items():
            data["words"][word_type.name.lower()] = word_data.serialize()
        return data

class WiktionaryWordData:
    """
    Data representing information for a single word type for term.
    """
    def __init__(self, name: AccentedText, word_type: WordType):
        self.name = AccentedText(name)
        self.word_type = word_type
        self.declension = None
        self.definitions = []
        self.related_terms = []
        self.derived_terms = []
        self.synonyms = []
        self.antonyms = []

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "name": self.name.raw,
            "definitions": [x.serialize() for x in self.definitions],
        }
        if self.related_terms:
            data["related_terms"] = [term.raw for term in self.related_terms]
        if self.derived_terms:
            data["derived_terms"] = [term.raw for term in self.derived_terms]
        if self.synonyms:
            data["synonyms"] = [term.raw for term in self.synonyms]
        if self.antonyms:
            data["antonyms"] = [term.raw for term in self.antonyms]
        return data


class WiktionaryWordDefinition:
    """
    Data representing a definition for a word.
    """
    def __init__(self):
        self.definition = AccentedText()
        self.examples = []

    def serialize(self) -> dict:
        """Serialize the state of this object into a dictionary."""
        data = {
            "definition": self.definition.raw,
        }
        if self.examples:
            data["examples"] = []
            for russian, english in self.examples:
                data["examples"].append({
                    "ru": russian.raw,
                    "en": english.raw})
        return data


class WiktionarySection:
    def __init__(self, depth: int, parent, tag, name: str):
        self.depth = depth
        self.parent = parent
        self.tag = tag
        self.name = name
        self.elements = []
        self.children = []
        if self.parent:
            self.parent.children.append(self)

    def __iter__(self):
        for child in self.children:
            yield child.name

    def __getitem__(self, name):
        for child in self.children:
            if name == child.name:
                return child
        raise KeyError(name)

    @property
    def contents(self) -> str:
        result = ""
        for element in self.elements:
            result += element.text
        return result

    def items(self):
        for child in self.children:
            yield child.name, child

    def print_all(self, prefix=""):
        result = prefix + repr(self) + "\n"
        for child in self.children:
            result += child.print_all(prefix=prefix + "  ")
        return result

    def __repr__(self):
        return "<{}({}, {}, {} elements)>".format(
            self.__class__.__name__,
            self.depth,
            self.name,
            len(self.elements))

def parse_term_list(section) -> list:
    """Parses a list of terms."""
    if len(section.elements) == 0:
        return []
    terms = []
    terms_list = section.elements[0]
    for russian in terms_list.find_all(attrs={"lang": "ru"}):
        term = AccentedText(russian.text.lower().strip())
        terms.append(term)
    return terms

def parse_noun_declension_table(section: WiktionarySection) -> Noun:
    """
    Parses declension info for a noun from a table.
    """
    div = section.elements[0]
    noun = Noun()
    for row in div.find_all("tr"):
        try:
            case = types.parse_case(row.th.text.lower().strip())
        except ValueError:
            continue
        forms = []
        for form in row.find_all("td"):
            form = form.find(attrs={"lang": "ru"})
            forms.append(AccentedText(form.text.strip()))
        
        if len(forms) >= 1:
            noun.set_declension(case=case, plurality=Plurality.Singular, declension=forms[0])
        if len(forms) >= 2:
            noun.set_declension(case=case, plurality=Plurality.Plural, declension=forms[1])
    return noun

def parse_adjective_declension_table(section: WiktionarySection) -> Adjective:
    """
    Parses declension info for a adjective from a table.
    """
    div = section.elements[0]
    adj = Adjective()
    for row in div.find_all("tr"):
        columns = row.find_all("td")
        if not columns:
            continue

        short = False
        case = None

        label = row.th.text.lower().strip()
        if "inanimate" in label:
            continue
        elif "animate" in label:
            case = Case.Accusative
        elif "short" in label:
            short = True
        else:
            try:
                case = types.parse_case(label)
            except ValueError:
                continue
        forms = []
        for column in columns:
            form = column.find(attrs={"lang": "ru"})
            span = 1
            if "colspan" in column.attrs:
                span = int(column.attrs["colspan"])
            if form:
                form_text = AccentedText(form.text.strip())
            else:
                forms_text = AccentedText()
            forms += [form_text] * span
        print(forms)
        assert len(forms) == 4
        
        adj.set_declension(case=case,
                           plurality=Plurality.Singular,
                           gender=Gender.Masculine,
                           short=short,
                           text=forms[0])
        adj.set_declension(case=case,
                           plurality=Plurality.Singular,
                           gender=Gender.Neuter,
                           short=short,
                           text=forms[1])
        adj.set_declension(case=case,
                           plurality=Plurality.Singular,
                           gender=Gender.Femanine,
                           short=short,
                           text=forms[2])
        adj.set_declension(case=case,
                           plurality=Plurality.Plural,
                           gender=None,
                           short=short,
                           text=forms[3])
    return adj

def parse_verb_conjugation_table(verb: Verb, section: WiktionarySection) -> Verb:
    """
    Parses a verb conjugation table into a Verb object.
    """
    div = section.elements[1]

    # Parse verb info from the header
    table_header = div.find(attrs={"class": "NavHead"})
    header_text = table_header.text.strip().lower()
    verb.transitive = "transitive" in header_text
    verb.reflexive = "reflexive" in header_text
    match = re.search("class (\S+)", header_text)
    if match:
        verb.conjugation_class = match.group(1)

    # Parse the conjugation table
    table_content = div.find(attrs={"class": "NavContent"})
    header = ""
    for row in table_content.find_all("tr"):
        # Parse table section header labels
        try:
            label = row.th.text.lower().strip()
        except:
            continue
        columns = row.find_all("td")
        if not columns:
            header = label
            if label == "imperfective aspect":
                verb.aspect = Aspect.Imperfective
            elif label == "perfective aspect":
                verb.aspect = Aspect.Perfective
            continue

        # Parse russian text from columns
        forms = []
        for column in columns:
            russian = column.find(attrs={"lang": "ru"})
            if russian:
                forms.append(AccentedText(russian.text.strip()))
            else:
                forms.append(AccentedText(""))

        # Load information from columns into verb conjugation
        side = 0
        if verb.aspect == Aspect.Perfective:
            side = 1
                
        if label == "infinitive":
            verb.infinitive = AccentedText(forms[0])
        elif "1st singular" in label:
            verb.set_non_past(plurality=Plurality.Singular,
                              person=Person.First,
                              text=AccentedText(forms[side]))
        elif "2nd singular" in label:
            verb.set_non_past(plurality=Plurality.Singular,
                              person=Person.Second,
                              text=AccentedText(forms[side]))
        elif "3rd singular" in label:
            verb.set_non_past(plurality=Plurality.Singular,
                              person=Person.Third,
                              text=AccentedText(forms[side]))
        elif "1st plural" in label:
            verb.set_non_past(plurality=Plurality.Plural,
                              person=Person.First,
                              text=AccentedText(forms[side]))
        elif "2nd plural" in label:
            verb.set_non_past(plurality=Plurality.Plural,
                              person=Person.Second,
                              text=AccentedText(forms[side]))
        elif "3rd plural" in label:
            verb.set_non_past(plurality=Plurality.Plural,
                              person=Person.Third,
                              text=AccentedText(forms[side]))
        elif header == "imperative":
            verb.imperative[Plurality.Singular] = forms[0]
            verb.imperative[Plurality.Plural] = forms[1]
        elif "masculine" in label:
            verb.set_past(plurality=Plurality.Singular,
                          gender=Gender.Masculine,
                          text=AccentedText(forms[0]))
            verb.set_past(plurality=Plurality.Plural,
                          gender=None,
                          text=AccentedText(forms[1]))
        elif "feminine" in label:
            verb.set_past(plurality=Plurality.Singular,
                          gender=Gender.Femanine,
                          text=AccentedText(forms[0]))
        elif "neuter" in label:
            verb.set_past(plurality=Plurality.Singular,
                          gender=Gender.Neuter,
                          text=AccentedText(forms[0]))
        elif "active" in label:
            verb.set_participle(participle=Participle.Active,
                                tense=Tense.Present,
                                text=AccentedText(forms[0]))
            verb.set_participle(participle=Participle.Active,
                                tense=Tense.Past,
                                text=AccentedText(forms[1]))
        elif "passive" in label:
            verb.set_participle(participle=Participle.Passive,
                                tense=Tense.Present,
                                text=AccentedText(forms[0]))
            verb.set_participle(participle=Participle.Passive,
                                tense=Tense.Past,
                                text=AccentedText(forms[1]))
        elif "adverbial" in label:
            verb.set_participle(participle=Participle.Adverbial,
                                tense=Tense.Present,
                                text=AccentedText(forms[0]))
            verb.set_participle(participle=Participle.Adverbial,
                                tense=Tense.Past,
                                text=AccentedText(forms[1]))
    
    return verb

def download_word(name: str):
    word_text = AccentedText(name).text.lower()
    url = "https://en.wiktionary.org/wiki/{}".format(word_text)
    soup = request_html(url)
    root = soup.body
    #russian = get_section(root, "h2", "Russian")
    #noun = get_section(root, "h3", "Noun")

    tree = {}
    tree_item = None
    
    body = root.find("div", attrs={"class": "mw-parser-output"})
    for child in body.children:
        if child.name is None:
            continue
        if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headline = child.find("span", attrs={"class": "mw-headline"})
            depth = int(child.name[1])
            header = headline.text.lower()
            while tree_item and depth <= tree_item.depth:
                tree_item = tree_item.parent
            section = WiktionarySection(tag=child, depth=depth, parent=tree_item, name=header)
            if section.parent is None:
                tree[section.name] = section
            tree_item = section
        elif tree_item:
            tree_item.elements.append(child)

    #print("")
    for section in tree.values():
        print(section.print_all())
        
    if "russian" not in tree:
        return None
    tree = tree["russian"]

    data = WiktionaryData(name=name)

    # Parse etymology information
    if "etymology" in tree:
        data.etymology = AccentedText(tree["etymology"].contents.strip())

    # Parse pronunciation information
    if "pronunciation" in tree:
        pronunciation_section = tree["pronunciation"]
        audiotable = pronunciation_section.elements[0].find(attrs={"class": "audiotable"})
        if audiotable:
            for source in audiotable.find_all("source"):
                url = "https:" + source["src"]
                extension = re.search("\.([a-zA-Z0-9]+)$", url)
                if extension:
                    extension = extension.group(1)
                data.audio_sources[extension] = url

    # Parse word type (Verb/Noun/Adverb/etc.) information
    for word_type in WordType:
        word_type_name = word_type.name.lower()
        if word_type_name not in tree:
            continue
        section = tree[word_type_name]

        word_data = WiktionaryWordData(name=name, word_type=word_type)
        word_info_tag = section.elements[0]
        accented_name_tag = word_info_tag.find(attrs={"lang": "ru"})
        if accented_name_tag:
            word_data.name = AccentedText(accented_name_tag.text.strip())
        word_info_text = word_info_tag.text.lower()

        # Parse info from word info text
        if word_type == WordType.Verb:
            verb = Verb()
            word_data.declension = verb
            match = re.search("\((?P<aspect>imperfective|perfective)\s+(?P<counterparts>.*?)\)", word_info_text)
            if match:
                aspect = match.group("aspect")
                counterparts = match.group("counterparts").split()
                for counterpart in counterparts:
                    counterpart = AccentedText(counterpart)
                    if has_russian_letters(counterpart):
                        verb.counterparts.append(counterpart)

        # Parse definitions
        ol = section.elements[1]
        for index, item in enumerate(ol.find_all("li")):
            definition_data = WiktionaryWordDefinition()
            examples = []
            definition_text = ""
            for x in item.children:
                if isinstance(x, NavigableString):
                    definition_text += str(x)
                else:
                    if x.name == "dl":
                        break
                    definition_text += x.text
            definition_data.definition = AccentedText(definition_text.strip())
            dl = item.find("dl")
            if dl:
                for ex in dl.find_all("dd"):
                    russian = ex.find(attrs={"lang": "ru"})
                    english = ex.find(attrs={"class": "e-translation"})
                    definition_data.examples.append(
                        (AccentedText(russian.text),
                         AccentedText(english.text)))
            word_data.definitions.append(definition_data)

        # Parse related/derived words/synonymns
        if "related terms" in section:
            word_data.related_terms += parse_term_list(section["related terms"])
        if "derived terms" in section:
            word_data.derived_terms += parse_term_list(section["derived terms"])
        if "synonyms" in section:
            word_data.synonyms += parse_term_list(section["synonyms"])
        if "antonyms" in section:
            word_data.antonyms += parse_term_list(section["antonyms"])

        # Parse declension/conjugation table
        if "declension" in section:
            declension_section = section["declension"]
            if word_type == WordType.Noun:
                word_data.declension = parse_noun_declension_table(declension_section)
            if word_type == WordType.Adjective:
                word_data.declension = parse_adjective_declension_table(declension_section)
        elif "conjugation" in section:
            conjugation_section = section["conjugation"]
            if word_type == WordType.Verb:
                word_data.declension = parse_verb_conjugation_table(verb, conjugation_section)

        data.words[word_type] = word_data

    return data
    
#word = download_word("открытка"))
#word = download_word("хотя бы")
word = download_word("красивый")
#print(str(download_word("знать")))
#print(str(download_word("бы")))

text = yaml.dump(word.serialize(), default_flow_style=False, allow_unicode=True).strip()
print(text)
