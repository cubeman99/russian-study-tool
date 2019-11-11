import requests
import threading
import traceback
import re
import yaml
from study_tool.config import Config
from study_tool.russian.word import AccentedText, has_russian_letters
from study_tool.russian.verb import VerbConjugation
from study_tool.russian.noun import NounDeclension
from study_tool.russian.adjective import AdjectiveDeclension
from study_tool.russian.types import WordType, Plurality, Case, Person, Aspect, Gender, Participle, Tense
from study_tool.russian import types
from study_tool.russian.story import Story, Chapter
from study_tool.external.wiktionary_term import WiktionaryTerm
from study_tool.external.wiktionary_term import WiktionaryWordData
from study_tool.external.wiktionary_term import WiktionaryWordDefinition
from study_tool.external.wiktionary_term import WiktionaryVerbData
from study_tool.external.wiktionary_term import WiktionaryNounData
from study_tool.external.wiktionary_term import WiktionaryAdjectiveData
from study_tool.external.wiktionary_term import WiktionaryPronounData


class WiktionarySection:
    def __init__(self, depth: int, parent, tag, name: str):
        self.depth = depth
        self.parent = parent
        self.tag = tag
        self.name = name
        self.children = []
        self.html = ""
        self.soup = WiktionaryParser.BeautifulSoup("<div></div>", "lxml")
        if self.parent:
            self.parent.children.append(self)

    def add_element(self, element):
        self.html += str(element)
        self.soup = WiktionaryParser.BeautifulSoup(self.html, "lxml")

    def find_all(self, *args, **kwargs):
        return self.soup.find_all(*args, **kwargs)

    def find(self, *args, **kwargs):
        return self.soup.find(*args, **kwargs)

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
        return self.soup.text

    def items(self):
        for child in self.children:
            yield child.name, child

    def print_all(self, prefix=""):
        result = prefix + repr(self) + "\n"
        for child in self.children:
            result += child.print_all(prefix=prefix + "  ")
        return result

    def __repr__(self):
        return "<{}({}, {}>".format(
            self.__class__.__name__,
            self.depth,
            self.name)


class WiktionaryParser:
    """
    Interface to downloading term information from Wiktionary.
    """
    WORD_TYPE_TO_WORD_DATA_CLASS = {
        WordType.Verb: WiktionaryVerbData,
        WordType.Noun: WiktionaryNounData,
        WordType.Adjective: WiktionaryAdjectiveData,
        WordType.Pronoun: WiktionaryPronounData,
    }

    BeautifulSoup = None
    NavigableString = None

    def __init__(self):
        self.__lock = threading.Lock()

    def setup_imports(self):
        """Import the required python modules."""
        with self.__lock:
            from bs4 import BeautifulSoup
            from bs4 import NavigableString
            WiktionaryParser.BeautifulSoup = BeautifulSoup
            WiktionaryParser.NavigableString = NavigableString
            
    def download_term(self, name: str) -> WiktionaryTerm:
        """
        Downloads information for a term.
        """
        word_text = AccentedText(name).text.lower()
        url = "https://en.wiktionary.org/wiki/{}".format(word_text)
        soup = self.__download_page(url)
        if "Wiktionary does not yet have an entry for" in soup.text:
            return None
        root = soup.body
        if root is None:
            return None
        
        # Convert sections into a hierarchy of WiktionarySection
        # based on header tags
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
                tree_item.add_element(child)

        # Make sure there is a "Russian" section
        if "russian" not in tree:
            return None
        tree = tree["russian"]
        data = WiktionaryTerm(name)

        # Parse etymology information
        if "etymology" in tree:
            data.etymology = AccentedText(tree["etymology"].contents.strip())

        # Parse pronunciation information
        if "pronunciation" in tree:
            pronunciation_section = tree["pronunciation"]
            audiotable = pronunciation_section.find(attrs={"class": "audiotable"})
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

            if word_type in self.WORD_TYPE_TO_WORD_DATA_CLASS:
                word_data = self.WORD_TYPE_TO_WORD_DATA_CLASS[word_type](name)
            else:
                word_data = WiktionaryWordData(text=name, word_type=word_type)
            word_info_tag = section.find("p")
            accented_name_tag = word_info_tag.find(attrs={"lang": "ru"})
            if accented_name_tag:
                word_data.name = AccentedText(accented_name_tag.text.strip())
            word_info_text = word_info_tag.text.lower()

            # Parse definitions
            ol = section.find("ol")
            for index, item in enumerate(ol.find_all("li")):
                definition_data = WiktionaryWordDefinition()
                examples = []
                definition_text = ""
                for x in item.children:
                    if isinstance(x, self.NavigableString):
                        definition_text += str(x)
                    else:
                        if x.name == "dl":
                            break
                        definition_text += x.text
                definition_data.definition = AccentedText(definition_text.strip())
                dl = item.find("dl")
                if dl:
                    for ex in dl.find_all("dd", recursive=False):
                        russian = ex.find(attrs={"lang": "ru"})
                        english = ex.find(attrs={"class": "e-translation"})
                        if english and russian:
                            definition_data.examples.append(
                                (AccentedText(russian.text),
                                 AccentedText(english.text)))
                word_data.definitions.append(definition_data)

            # Parse related/derived words/synonymns
            if "related terms" in section:
                word_data.related_terms += self.parse_term_list(section["related terms"])
            if "derived terms" in section:
                word_data.derived_terms += self.parse_term_list(section["derived terms"])
            if "synonyms" in section:
                word_data.synonyms += self.parse_term_list(section["synonyms"])
            if "antonyms" in section:
                word_data.antonyms += self.parse_term_list(section["antonyms"])

            if word_type == WordType.Verb:
                verb = word_data
                # Parse info from word info text
                match = re.search("\((?P<aspect>imperfective|perfective)\s+(?P<counterparts>.*?)\)", word_info_text)
                if match:
                    aspect = match.group("aspect")
                    counterparts = match.group("counterparts").split()
                    for counterpart in counterparts:
                        counterpart = AccentedText(counterpart)
                        if has_russian_letters(counterpart):
                            verb.counterparts.append(counterpart)

                # Parse verb conjugation table
                if "conjugation" in section:
                    conjugation_section = section["conjugation"]
                    verb.conjugation = self.parse_verb_conjugation_table(conjugation_section)

            elif word_type == WordType.Noun:
                noun = word_data
                # Parse noun declension table
                if "declension" in section:
                    declension_section = section["declension"]
                    noun.declension = self.parse_noun_declension_table(declension_section)
                    
            elif word_type == WordType.Adjective:
                adjective = word_data
                # Parse adjective declension table
                if "declension" in section:
                    declension_section = section["declension"]
                    adjective.declension = self.parse_adjective_declension_table(declension_section)
                    
            elif word_type == WordType.Pronoun:
                pronoun = word_data
                # Parse pronoun declension table
                if "declension" in section:
                    declension_section = section["declension"]
                    pronoun.declension = self.parse_adjective_declension_table(declension_section)

            data.words[word_type] = word_data

        return data

    @classmethod
    def parse_term_list(cls, section) -> list:
        """Parses a list of terms."""
        terms = []
        for russian in section.find_all(attrs={"lang": "ru"}):
            term = AccentedText(russian.text.lower().strip())
            terms.append(term)
        return terms
    
    @classmethod
    def parse_noun_declension_table(cls, section: WiktionarySection) -> NounDeclension:
        """
        Parses declension info for a noun from a table.
        """
        nav_frame = section.find(attrs={"class": "NavFrame"})
        noun = NounDeclension()
        # Parse each row in the table
        label = ""
        for row in nav_frame.find_all("tr"):
            columns = row.find_all("td")
            if not columns:
                continue

            header = row.th
            if header:
                label = header.text.lower().strip()
                if "accusative" in label:
                    label = "accusative"
                # TODO: Locative case
                try:
                    case = types.parse_case(label.strip())
                except ValueError:
                    continue
            else:
                assert "accusative" in label

            forms = []
            for form in columns:
                form = form.find(attrs={"lang": "ru"})
                forms.append(AccentedText(form.text.strip()))
        
            if len(forms) >= 1:
                noun.set_declension(case=case, plural=Plurality.Singular, text=forms[0])
            if len(forms) >= 2:
                noun.set_declension(case=case, plural=Plurality.Plural, text=forms[1])
        return noun
    
    @classmethod
    def parse_adjective_declension_table(cls, section: WiktionarySection) -> AdjectiveDeclension:
        """
        Parses declension info for a adjective from a table.
        """
        nav_frame = section.find(attrs={"class": "NavFrame"})
        adj = AdjectiveDeclension()
        for row in nav_frame.find_all("tr"):
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
    
    @classmethod
    def parse_verb_conjugation_table(cls, section: WiktionarySection) -> VerbConjugation:
        """
        Parses a verb conjugation table into a Verb object.
        """
        nav_frame = section.find(attrs={"class": "NavFrame"})
        verb = VerbConjugation()

        # Parse verb info from the header
        table_header = nav_frame.find(attrs={"class": "NavHead"})
        header_text = table_header.text.strip().lower()
        #verb.transitive = "transitive" in header_text
        #verb.reflexive = "reflexive" in header_text
        match = re.search("class (\S+)", header_text)
        if match:
            verb.conjugation_class = match.group(1)

        # Parse the conjugation table
        table_content = nav_frame.find(attrs={"class": "NavContent"})
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
                verb.set_non_past(plural=Plurality.Singular,
                                  person=Person.First,
                                  text=AccentedText(forms[side]))
            elif "2nd singular" in label:
                verb.set_non_past(plural=Plurality.Singular,
                                  person=Person.Second,
                                  text=AccentedText(forms[side]))
            elif "3rd singular" in label:
                verb.set_non_past(plural=Plurality.Singular,
                                  person=Person.Third,
                                  text=AccentedText(forms[side]))
            elif "1st plural" in label:
                verb.set_non_past(plural=Plurality.Plural,
                                  person=Person.First,
                                  text=AccentedText(forms[side]))
            elif "2nd plural" in label:
                verb.set_non_past(plural=Plurality.Plural,
                                  person=Person.Second,
                                  text=AccentedText(forms[side]))
            elif "3rd plural" in label:
                verb.set_non_past(plural=Plurality.Plural,
                                  person=Person.Third,
                                  text=AccentedText(forms[side]))
            elif header == "imperative":
                verb.set_imperative(plural=Plurality.Singular, text=forms[0])
                verb.set_imperative(plural=Plurality.Plural, text=forms[1])
            elif "masculine" in label:
                verb.set_past(plural=Plurality.Singular,
                              gender=Gender.Masculine,
                              text=AccentedText(forms[0]))
                verb.set_past(plural=Plurality.Plural,
                              gender=None,
                              text=AccentedText(forms[1]))
            elif "feminine" in label:
                verb.set_past(plural=Plurality.Singular,
                              gender=Gender.Femanine,
                              text=AccentedText(forms[0]))
            elif "neuter" in label:
                verb.set_past(plural=Plurality.Singular,
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
    
    def __download_page(self, url: str):
        """Downloads an html page."""
        self.setup_imports()
        response = requests.get(url)
        soup = self.BeautifulSoup(response.text, features="lxml")
        return soup
