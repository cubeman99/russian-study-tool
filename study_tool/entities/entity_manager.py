import cmg
from cmg.color import Colors
from study_tool.entities.entity import Entity


class EntityManager:
    """
    Manages entities.
    """

    def __init__(self, context=None):
        self.__entities = []
        self.__context = context
        self.__enities_to_delete = []
        self.__show_entity_outlines = False

    def add_entity(self, entity: Entity, pos=None):
        """Adds a new entity."""
        entity.init(manager=self, context=self.__context, pos=pos)
        self.__entities.append(entity)
        return entity

    def update(self, dt: float):
        """
        Updates all entities.
        """
        # Update entities
        self.__enities_to_delete = []
        entity_list = list(self.__entities)
        for entity in entity_list:
            self.__update_entity(entity, dt)

        # Remove destroyed entities
        for entity in self.__enities_to_delete:
            if entity.get_parent():
                entity.get_parent().remove_child(entity)
            else:
                self.__entities.remove(entity)

    def __update_entity(self, entity: Entity, dt: float):
        """
        Updates a single entity and all its children.
        """
        if not entity.is_destroyed():
            entity.update(dt)
            for child in entity.get_children():
                self.__update_entity(child, dt)
        if entity.is_destroyed():
            self.__enities_to_delete.append(entity)

    def draw(self, g):
        """
        Draws all entities.
        """
        for entity in self.__entities:
            self.__draw_entity(entity, g)

    def __draw_entity(self, entity: Entity, g):
        """
        Draws a single entity and all its children.
        """
        if not entity.is_destroyed() and entity.is_visible():
            entity.draw(g)
            if self.__show_entity_outlines:
                rect = entity.get_rect()
                g.draw_rect(rect, color=Colors.RED)
            for child in entity.get_children():
                self.__draw_entity(child, g)
