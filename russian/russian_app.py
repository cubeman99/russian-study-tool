
import pygame
import time
from cmg.input import *
from cmg.graphics import *
from cmg.application import *
from enum import IntEnum
from russian.types import *
from russian.words import *

# Define some colors
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)

class RussianApp(Application):

  def __init__(self):
    Application.__init__(self, title="Russian", width=800, height=600)
    self.textPrint = TextPrint()
    self.words = self.load_words("data/adjectives.txt",
                                 word_type=WordType.Adjective)
    self.wordOrder = []
    self.currentWord = None
    self.currentIndex = 0
    self.wordOrder = list(self.words)
    self.currentWord = self.wordOrder[0]
    self.side = Language.English

    self.input.bind(pygame.K_ESCAPE, pressed=self.quit)
    self.input.bind(pygame.K_SPACE, pressed=self.flip)
    self.input.bind(pygame.K_RETURN, pressed=self.next)

  def flip(self):
    """
    Flip the flashcard over.
    """
    self.side = (Language.English if self.side == Language.Russian
                 else Language.Russian)

  def next(self):
    """
    Move to the next card.
    """
    self.currentIndex = (self.currentIndex + 1) % len(self.wordOrder)
    self.currentWord = self.wordOrder[self.currentIndex]
    self.side = Language.English

  def load_words(self, path, word_type=WordType.Noun):
    words = []
    with open(path, "r", encoding="utf8") as f:
      lines = f.read().splitlines()
      lines = [l.strip() for l in lines if len(l.strip()) > 0]
      for line in lines:
        tokens = [t.strip() for t in line.split("-")]
        if len(tokens) == 2:
          word = Word(russian=tokens[0],
                      english=tokens[1],
                      word_type=word_type)
          words.append(word)
    return words

  def update(self, dt):
    pass

  def draw(self):
    self.screen.fill(WHITE)
    self.textPrint.reset()
    
    text = None
    if self.side == Language.English:
      text = self.currentWord.english
    else:
      text = self.currentWord.russian
    self.textPrint.print(self.screen, text)
        
