from study_tool.russian.types import *
from study_tool.russian.word import AccentedText

CONSONANTS = "б,в,г,д,ж,з,к,л,м,н,п,р,с,т,ф,х,ц,ч,ш,щ,й"
VOWELS = "а,э,ы,у,о,я,е,ё,ю,и".split(",")
ACCENT_CHAR = "´"
ACCENT_CHARS = "'´`"
HARD_VOWELS = "аоуыэ"
SOFT_VOWELS = "яёюие"
TO_SOFT = {"а": "я",
           "о": "ё",
           "у": "ю",
           "ы": "и",
           "э": "е"}

def simplify(word):
  word = word.lower()
  stress = None
  for c in ACCENT_CHARS:
    if c in word:
      stress = word.index(c) - 1
      word = word.replace(c, "")
  return word, stress

def decline_adjective(adj: AccentedText,
                      case=Case.Nominative,
                      gender=Gender.Masculine,
                      plurality=Plurality.Singular,
                      animacy=Animacy.Inanimate,
                      short=False):
  adj, stress = simplify(repr(adj))
  end_stressed = stress == len(adj) - 2
  if not (adj.endswith("ый") or adj.endswith("ой") or adj.endswith("ий")):
    return AccentedText(adj)
  stem = adj[:-2]
  a = "а"
  y = "у"
  s1 = "о"
  s2 = "ы"
  if adj[-2] == "и" and stem[-1] == "н":  # soft Н
    s1 = "е"
    s2 = "и"
    a = "я"
    y = "ю"
  else:
    if stem[-1] in "гкхшщчжц":
      s2 = "и"
    if stem[-1] in "шщчжц" and not end_stressed:
      s1 = "е"

  if short:
    if adj == "большой":
      stem = "велик"
      stress = 3
      end_stressed = True
    elif adj == "маленький":
      stem = "мал"
      stress = 1
      end_stressed = True
    if plurality == Plurality.Plural:
      result = stem + s2
    elif gender == Gender.Masculine:
      if stem[-2] in CONSONANTS:
        if stem[-1] == "н":
          result = stem[:-1] + "е" + stem[-1]
        else:
          result = stem[:-1] + "о" + stem[-1]
      else:
        result = stem
    elif gender == Gender.Femanine:
      result = stem + a
    elif gender == Gender.Neuter:
      result = stem + s1
  else:
    if gender == Gender.Masculine and animacy == Animacy.Animate:
      case = Case.Genetive
    if case == Case.Nominative:
      if plurality == Plurality.Plural:
        result = stem + s2 + "е"
      elif gender == Gender.Masculine:
        result = adj
      elif gender == Gender.Femanine:
        result = stem + a + "я"
      elif gender == Gender.Neuter:
        result = stem + s1 + "е"
    elif case == Case.Accusative:
      if plurality == Plurality.Plural:
        if animacy == Animacy.Animate:
          result = stem + s2 + "х"
        else:
          result = stem + s2 + "е"
      elif gender == Gender.Femanine:
        result = stem + y + "ю"
      elif gender == Gender.Neuter:
        result = stem + s1 + "е"
      elif animacy == Animacy.Animate:
        result = stem + s1 + "го"
      else:
        result = adj
    elif case == Case.Genetive:
      if plurality == Plurality.Plural:
        result = stem + s2 + "х"
      elif gender == Gender.Femanine:
        result = stem + s1 + "й"
      else:
        result = stem + s1 + "го"
    elif case == Case.Dative:
      if plurality == Plurality.Plural:
        result = stem + s2 + "м"
      elif gender == Gender.Femanine:
        result = stem + s1 + "й"
      else:
        result = stem + s1 + "му"
    elif case == Case.Prepositional:
      if plurality == Plurality.Plural:
        result = stem + s2 + "х"
      elif gender == Gender.Femanine:
        result = stem + s1 + "й"
      else:
        result = stem + s1 + "м"
    elif case == Case.Instrumental:
      if plurality == Plurality.Plural:
        result = stem + s2 + "ми"
      elif gender == Gender.Femanine:
        result = stem + s1 + "й"
      else:
        result = stem + s2 + "м"
  if stress is not None:
    return AccentedText(result[:stress + 1] + ACCENT_CHAR + result[stress + 1:])
  else:
    return AccentedText(result)


#column_width = 20
##for adj in ["но´вый", "си´ний", "ру´сский", "хоро´ший", "большо´й"]:
#for adj in ["интере´сный", "гро´мкий", "широ´кий", "мале´нький", "большо´й"]:
#  rows = [["", "masculine", "neuter", "femanine", "plural"]]
#  for case in [Case.Nominative, Case.Accusative, Case.Genetive, Case.Prepositional, Case.Dative, Case.Instrumental]:
#    animacies = [Animacy.Inanimate]
#    if case == Case.Accusative:
#      animacies.append(Animacy.Animate)
#    for animacy in animacies:
#      row = [case.name]
#      row.append(decline_adjective(adj, case=case, gender=Gender.Masculine, animacy=animacy))
#      row.append(decline_adjective(adj, case=case, gender=Gender.Neuter, animacy=animacy))
#      row.append(decline_adjective(adj, case=case, gender=Gender.Femanine, animacy=animacy))
#      row.append(decline_adjective(adj, case=case, plurality=Plurality.Plural, animacy=animacy))
#      rows.append(row)
#  row = ["Short"]
#  row.append(decline_adjective(adj, short=True, gender=Gender.Masculine))
#  row.append(decline_adjective(adj, short=True, gender=Gender.Neuter))
#  row.append(decline_adjective(adj, short=True, gender=Gender.Femanine))
#  row.append(decline_adjective(adj, short=True, plurality=Plurality.Plural))
#  rows.append(row)
#  for row in rows:
#    line = ""
#    for col in row:
#      line += ("{:" + str(column_width) + "}").format(col)
#    print(line)
#  print("")

#exit(0)