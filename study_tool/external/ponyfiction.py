import requests
import traceback
import re
from bs4 import BeautifulSoup
from study_tool.config import Config
from study_tool.russian.story import Story, Chapter


def request_html(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, features="lxml")
  return soup


def download_chapter(story_id: int, chapter: int):
  try:
    url = "https://ponyfiction.org/story/{}/chapter/{}/".format(story_id, chapter)
    soup = request_html(url)
    root = soup.body
    story = root.find("div", attrs={"class": "chapter-text chapter-text-block js-story-formatting"})
    if story is None:
      return None
    title = story.find("h1").text.strip()
    chapter = Chapter(title=title, number=chapter)
    for para in story.find_all("p"):
      if len(para.attrs) == 0:
        chapter.paragraphs.append(para.text.strip())
    return chapter
  except:
    Config.logger.error("Error downloading story {} chapter {}"
                        .format(story_id, chapter))
    traceback.print_exc()
    return None
    

def download_story(story_id: int):
  try:
    url = "https://ponyfiction.org/story/{}/".format(story_id)
    soup = request_html(url)
    root = soup.body
    title_element = root.find("h1", attrs={"id": "story_title"})
    name_element = root.find("span", attrs={"itemprop": "name"})
    title = name_element.text.strip()

    story = Story(story_id=story_id, title=title)

    chapter_number = 1
    while True:
      print(chapter_number)
      chapter = download_chapter(story_id=story.story_id,
                                 chapter=chapter_number)
      if chapter is None:
        break
      story.chapters.append(chapter)
      chapter_number += 1
    return story
  except:
    Config.logger.error("Error downloading story {} chapter {}"
                        .format(story_id, chapter))
    traceback.print_exc()
    return None

