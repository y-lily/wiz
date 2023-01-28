from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import Any

from typing_extensions import override

from .character_controller import (
    AnimationController,
    HeroMovementController,
    MovementController,
    NPCMovementController,
)
from .entity import MovingEntity
from .lua_defs import LuaCharacterTable, Trigger
from .shared import Controller


class Character(ABC):
    """
    In order to use Character, implement the _load_controllers method.

    """

    def __init__(self, name: str, entity: MovingEntity, trigger: Trigger | None = None) -> None:

        self._name = name
        self._entity = entity
        self._controllers: list[Controller]
        self._trigger = trigger

    @abstractproperty
    def movement_controller(self) -> MovementController[Any]:
        pass

    @property
    def entity(self) -> MovingEntity:
        return self._entity

    @property
    def trigger(self) -> Trigger | None:
        return self._trigger

    def update(self, dt: float) -> None:
        for controller in self._controllers:
            controller.update(dt)

    @abstractmethod
    def load_controllers(self, char_table: LuaCharacterTable) -> None:
        """Load animation and movement controllers here."""
        self._controllers = []
        self._controllers.append(AnimationController(entity=self._entity))


class Hero(Character):

    @property
    def movement_controller(self) -> HeroMovementController:
        return self._movement_controller

    @override
    def load_controllers(self, char_table: LuaCharacterTable) -> None:
        super().load_controllers(char_table)
        state_table = char_table.defined_states
        initial = char_table.state
        self._movement_controller = HeroMovementController(
            model=self._entity, state_table=state_table, initial=initial)
        self._controllers.append(self._movement_controller)


class NPC(Character):

    @property
    def movement_controller(self) -> NPCMovementController:
        return self._movement_controller

    @override
    def load_controllers(self, char_table: LuaCharacterTable) -> None:
        super().load_controllers(char_table)
        state_table = char_table.defined_states
        initial = char_table.state
        self._movement_controller = NPCMovementController(
            model=self._entity, state_table=state_table, initial=initial)
        self._controllers.append(self._movement_controller)
