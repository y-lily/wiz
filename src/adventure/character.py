from __future__ import annotations

from pygame.event import Event

from .blueprint import AdventureMapTrigger
from .character_controller import MovementController
from .entity import MovingEntity
from .shared import Controller


class Character:

    def __init__(self, name: str, entity: MovingEntity, trigger: AdventureMapTrigger | None = None) -> None:

        self._name = name
        self._entity = entity
        self._controllers: list[Controller] = []
        self._trigger = trigger

    @property
    def movement_controller(self) -> MovementController:
        return self._movement_controller

    @property
    def entity(self) -> MovingEntity:
        return self._entity

    @property
    def trigger(self) -> AdventureMapTrigger | None:
        return self._trigger

    def add_controller(self, controller: Controller) -> None:
        self._controllers.append(controller)

    def add_movement_controller(self, controller: MovementController) -> None:
        self._movement_controller = controller
        self._controllers.append(controller)

    def update(self, dt: float) -> None:
        for controller in self._controllers:
            controller.update(dt)
