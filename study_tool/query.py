from study_tool.card import Card

class CardQuery:
    """
    Queries a list of cards.
    """

    def __init__(self, max_count=30, max_score=1.0,
                 max_proficiency=10, card_type=None):
        """
        Defines a study query
        """
        self.max_count = max_count
        self.max_score = max_score
        self.max_proficiency = max_proficiency
        self.card_type = None

    def matches(self, card: Card, study_data) -> bool:
        if self.card_type is not None and card.get_word_type() != self.card_type:
            return False
        if self.max_score is not None and study_data.get_history_score() > self.max_score:
            return False
        if self.max_proficiency is not None and study_data.get_proficiency_level() > self.max_proficiency:
            return False
        return True

