import sys

#from study_tool import conjugator
#conjugator.main()
#exit(0)

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
