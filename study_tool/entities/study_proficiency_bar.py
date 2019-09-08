import pygame
from cmg.color import Colors
from cmg.graphics import Align
from study_tool.config import Config
from study_tool.entities.entity import Entity

class StudyProficiencyBar(Entity):
    """
    Bar that displays the proficiency histogram of a study set.
    """

    def __init__(self, center_y, left, right, study_set):
        super().__init__()
        self.center_y = center_y
        self.left = left
        self.right = right
        self.study_set = study_set
        self.__proficiency_counts = {}
        self.__score = 0
        self.__total_cards = 0
        self.__font_bar_text = pygame.font.Font(None, 30)

    def on_create(self):
        """Called when the entity is created."""
        cards = []
        if isinstance(self.study_set, list):
            cards = self.study_set
        else:
            cards = list(self.study_set.cards)
        self.__total_cards = len(cards)

        self.__proficiency_counts = {}
        self.__score = 0
        for level in range(Config.proficiency_levels, -1, -1):
            count = len([c for c in cards if c.proficiency_level == level])
            self.__proficiency_counts[level] = count
            if count > 0:
                self.__score += count * max(0, level - 1)
        self.__score /= max(1.0, float((Config.proficiency_levels - 1) * len(cards)))
        self.__score = int(round(self.__score * 100))

    def update(self, dt):
        """Update the entity."""
            
    def draw(self, g):
        """Draw the entity."""
        cards = []
        if isinstance(self.study_set, list):
            cards = self.study_set
        else:
            cards = list(self.study_set.cards)
        total_cards = len(cards)

        font = self.__font_bar_text
        left_margin = g.measure_text("100%", font=font)[0] + 4
        right_margin = g.measure_text(str(9999), font=font)[0] + 4
        bar_height = g.measure_text("1", font=font)[1]
        bar_width = self.right - self.left - left_margin - right_margin
        top = self.center_y - (bar_height / 2)

        if False:
            cards = sorted(
                cards, key=lambda x: x.get_history_score(), reverse=True)
            for index, card in enumerate(cards):
                score = card.get_history_score()
                x = self.left + left_margin + bar_width * \
                    (float(index) / len(cards))
                w = max(1, math.ceil(float(bar_width) / len(cards)))
                c = math.lerp(Colors.RED, Colors.GREEN, score)
                h = math.ceil(score * bar_height)
                g.fill_rect(x, top + bar_height - h, w, h, color=c)
        else:
            x = self.left + left_margin
            for level in range(Config.proficiency_levels, -1, -1):
                count = self.__proficiency_counts[level]
                if count > 0:
                    level_width = int(
                        round(bar_width * (float(count) / self.__total_cards)))
                    if x + level_width > self.left + left_margin + bar_width:
                        level_width = (self.left + left_margin + bar_width) - x
                    g.fill_rect(x, top, level_width, bar_height,
                                color=Config.proficiency_level_colors[level])
                    x += level_width
        g.draw_text(self.left + left_margin - 4, self.center_y, text="{}%".format(self.__score),
                    color=Colors.BLACK, align=Align.MiddleRight, font=font)
        g.draw_text(self.right - right_margin + 4, self.center_y, text=str(self.__total_cards),
                    color=Colors.BLACK, align=Align.MiddleLeft, font=font)
