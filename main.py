import sys

#from cmg.test.unit_test_framework import run_all_tests
#from study_tool.tests import test_word_database
# run_all_tests([test_word_database])
# exit(0)

if len(sys.argv) > 1:
    which = sys.argv[1]
else:
    which = "study_tool"

if which == "study_tool":
    from study_tool.study_tool_app import StudyCardsApp
    app = StudyCardsApp()
elif which == "pedal_control":
    from pedal_control.pedal_control_app import PedalControlApp
    app = PedalControlApp()
else:
    raise KeyError(which)

app.run()
