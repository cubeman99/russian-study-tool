from study_tool.russian.word import AccentedText


class Chapter:
    def __init__(self, title="", number=1):
        self.title = AccentedText(title)
        self.number = number
        self.paragraphs = []

    def serialize(self):
        return {"title": repr(self.title),
                "number": self.number,
                "paragraphs": [repr(p) for p in self.paragraphs]}

    def deserialize(self, state):
        self.title = AccentedText(state["title"])
        self.number = state["number"]
        self.paragraphs = list(AccentedText(p) for p in state["paragraphs"])


class Story:
    def __init__(self, story_id=0, title=""):
        self.story_id = story_id
        self.title = AccentedText(title)
        self.url = ""
        self.chapters = []

    def serialize(self):
        return {"title": repr(self.title),
                "id": self.story_id,
                "chapters": [c.serialize() for c in self.chapters]}

    def deserialize(self, state):
        self.title = AccentedText(state["title"])
        self.story_id = state["id"]
        self.chapters = []
        for chapter_state in state["chapters"]:
            chapter = Chapter()
            chapter.deserialize(chapter_state)
            self.chapters.append(chapter)
