
class Chapter:
  def __init__(self, title="", number=1):
    self.title = title
    self.number = number
    self.paragraphs = []

  def serialize(self):
    return {"title": self.title,
            "number": self.number,
            "paragraphs": self.paragraphs}
  
  def deserialize(self, state):
    self.title = state["title"]
    self.number = state["number"]
    self.paragraphs = list(state["paragraphs"])

    
class Story:
  def __init__(self, story_id=0, title=""):
    self.story_id = story_id
    self.title = title
    self.url = ""
    self.chapters = []
    
  def serialize(self):
    return {"title": self.title,
            "id": self.story_id,
            "chapters": [c.serialize() for c in self.chapters]}
  
  def deserialize(self, state):
    self.title = state["title"]
    self.story_id = state["id"]
    self.chapters = []
    for chapter_state in state["chapters"]:
      chapter = Chapter()
      chapter.deserialize(chapter_state)
      self.chapters.append(chapter)
