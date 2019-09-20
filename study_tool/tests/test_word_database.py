from cmg.test.unit_test_framework import *
from study_tool.russian.types import *
from study_tool.russian.word import *
from study_tool.word_database import *

VERB_CLASSIFICATIONS = {
VerbSuffix.Ai: ["бегать",
  "объяснять",
  "вспоминать",
  "опаздывать",
  "встречать",
  "отвечать",
  "выступать",
  "отдыхать",
  "гулять",
  "повторять",
  "делать",
  "покупать",
  "думать",
  "помогать",
  "завтракать",
  "понимать",
  "заниматься",
  "посылать",
  "знать",
  "работать",
  "играть",
  "решать",
  "кончать",
  "слушать",
  "мечтать",
  "собирать",
  "начинать",
  "спрашивать",
  "обедать",
  "ужинать",
  "обсуждать",
  "читать",
  "получать",
  "рассказывать"],

VerbSuffix.Ei: ["бедне´ть",
  "неме´ть",
  "беле´ть",
  "полне´ть",
  "бледне´ть",
  "пусте´ть",
  "богате´ть",
  "пьяне´ть",
  "боле´ть",
  "реде´ть",
  "веселе´ть",
  "робе´ть",
  "владе´ть",
  "слабе´ть",
  "голубе´ть",
  "сме´ть",
  "гре´ть",
  "старе´ть",
  "жале´ть",
  "тепле´ть",
  "желте´ть",
  "уме´ть",
  "здорове´ть",
  "успе´ть",
  "име´ть",
  "худе´ть",
  "красне´ть",
  "ясне´ть",
  "лысе´ть"],

VerbSuffix.Ova: ["рискова'ть",
  "анализи´ровать",
  "копи´ровать",
  "арестова´ть",
  "легализова´ть",
  "волнова´ться",
  "организова´ть",
  "гаранти´ровать",
  "ночева´ть",
  "горева´ть",
  "пакова´ть",
  "де´йствовать",
  "паркова´ть",
  "жа´ловаться",
  "практикова´ться",
  "импорти´ровать",
  "приватизи´ровать",
  "интересова´ться",
  "про´бовать",
  "комбини´ровать",
  "путеше´ствовать",
  "ра´довать",
  "танцева´ть",
  "реклами´ровать",
  "тре´бовать",
  "рекомендова´ть",
  "уча´ствовать",
  "ремонти´ровать",
  "чу´вствовать",
  "рисова´ть",
  "фотографи´ровать",
  "сле´довать",
  "экспорти´ровать",
  "сове'товать"],

VerbSuffix.Nu: ["верну´ться",
  "ло´пнуть",
  "взгляну´ть",
  "отдохну´ть",
  "вздохну´ть",
  "просну´ться",
  "вы´кинуть",
  "пры´гнуть",
  "вы´нуть",
  "рискну´ть",
  "дёрнуть",
  "ру´хнуть",
  "засну´ть",
  "улыбну´ться",
  "кри´кнуть",
  "шагну´ть",
  # Shifting stress
  "тону´ть",
  "тяну´ть",
  "помяну´ть"],

VerbSuffix.Nu2: ["блёкнуть",
  "кре´пнуть",
  "га´снуть",
  "мёрзнуть",
  "ги´бнуть",
  "мо´кнуть",
  "гло´хнуть",
  "па´хнуть",
  "дости´гнуть",
  "привы´кнуть",
  "замо´лкнуть",
  "сле´пнуть",
  "ки´снуть",
  "со´хнуть"],
 
VerbSuffix.A1: [# (a) those that are preceded by a vocalic root and whose root-final
  # consonant
  #     alternates (пис-/пиш-/писа´ть",
  "писа´ть",
  "маха´ть",
  "ре´зать",
  "сказа´ть",
  "пла´кать",
  "пря´тать",
  "шепта´ть",
  "щекота´ть",
  "иска´ть",
  "сы´пать",
  "колеба´ть",
  "дрема´ть"],
 
VerbSuffix.A2: [# (b) those with a vocalic root ending in й, and so the suffix is spelled
  #     я (й 1 а) (надея-ся/наде´яться",
  "се´ять",
  "наде´яться",
  "смея´ться",
  "ла´ять",
  "та´ять"],
 
VerbSuffix.A3: [# (c) those that are preceded by a nonvocalic root (жд-/жда´ть",
  "вра´ть",
  "жда´ть",
  "жра´ть",
  "лга´ть",
  "рва´ть",
  "ржа´ть",
  # Three verbs in this group have an inserted root vowel in the non-past
  "бра´ть",
  "дра´ть",
  "зва´ть"],

VerbSuffix.Avai: [# (a) Verbs with the root -да
  "отдава´ть",
  "преподава´ть",
  "передава´ть",
  "продава´ть",
  "подава´ть",
  "раздава´ться",
  # (b) Verbs with the root -зна
  "признава´ть",
  "сознава´ть",
  "узнава´ть",
  # (c) Verbs with the root -ста
  "встава´ть",
  "остава´ться",
  "отстава´ть",
  "перестава´ть",
  "устава´ть"],

VerbSuffix.O: ["боро´ться",
  "коло´ть",
  "моло´ть",
  "поло´ть",
  "поро´ть"],

VerbSuffix.I: [# Yes consonant mutation
  "ходи´ть",
  "вози´ть",
  "носи´ть",
  "плати´ть",
  "чи´стить",
  "люби´ть",
  "гото´вить",
  "лови´ть",
  "ста´вить",
  "корми´ть",
  "купи´ть",
  # No consonant mutation
  "вари´ть",
  "говори´ть",
  "жени´ться",
  "кури´ть",
  "учи´ть",
  "хвали´ть"],

VerbSuffix.E: [# Yes consonant mutation
  "ви´деть",
  "висе´ть",
  "зави´сеть",
  "лете´ть",
  "свисте´ть",
  "терпе´ть",
  "храпе´ть",
  "шуме´ть",
  # No consonant mutation
  "боле´ть",
  "горе´ть",
  "смотре´ть"],

VerbSuffix.Zha: ["боя´ться",
  "держа´ть",
  "дрожа´ть",
  "дыша´ть",
  "звуча´ть",
  "крича´ть",
  "молча´ть",
  "слы´шать",
  "стоя´ть",
  "стуча´ть"],
}

#def test_verb_classification():
#  root_path = "data"
#  word_data_file_name = "word_data.json"
#
#  wd = WordDatabase()
#  path = os.path.join(root_path, word_data_file_name)
#  wd.load(path)
#
#  for expected_suffix, verbs in VERB_CLASSIFICATIONS.items():
#    print(expected_suffix)
#    for verb in verbs:
#      verb = AccentedText(verb)
#      if verb.text in wd.words:
#        actual_suffix = wd[verb].classify_conjugation()
#        if actual_suffix != expected_suffix:
#          print("  " + verb)
#        expect_eq(actual=actual_suffix,
#                  expected=expected_suffix)
#      else:
#        verb = wd.add_verb(verb)
#        if verb is not None:
#             wd.save(path)

from study_tool.russian.word import WordPattern


def test_word_match():
    pattern = WordPattern("до того как")
    assert pattern.match("до того как")
    assert pattern.match("я до того, как он")
    assert not pattern.match("до того кака")
    assert not pattern.match("пдо того как")
    
    pattern = WordPattern("до (сих|тех) пор")
    assert pattern.match("до сих пор")
    assert pattern.match("до тех, пор")
    assert pattern.match("до тех пор пора")
    assert not pattern.match("до сихх пор")
    assert not pattern.match("до сихтех пор")
    
    pattern = WordPattern("все")
    assert pattern.match("все")
    assert pattern.match("всё")
    assert not pattern.match("всн")
    pattern = WordPattern("всё")
    assert pattern.match("все")
    assert pattern.match("всё")
    assert not pattern.match("всн")

if __name__ == "__main__":
    test_word_match()
