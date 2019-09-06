from cmg.math import Vec2


class EntityManager:
    """
    Manages entities.
    """

    def __init__(self, context=None):
        self.__entities = []
        self.__context = context

    def add_entity(self, entity, pos=None):
        """Adds a new entity."""
        entity.init(manager=self, context=self.__context, pos=pos)
        self.__entities.append(entity)
        return entity

    def update(self, dt: float):
        """
        Updates all entities.
        """
        # Update entities
        enities_to_delete = []
        entity_list = list(self.__entities)
        for entity in entity_list:
            if not entity.is_destroyed():
                entity.update(dt)
            if entity.is_destroyed():
                enities_to_delete.append(entity)

        # Remove destroyed entities
        for entity in enities_to_delete:
            self.__en
            tities.remove(entity)
            index += 1

    def draw(self, g):
        """
        Draws all entities.
        """
        for entity in self.__entities:
            if not entity.is_destroyed():
                entity.draw(g)
