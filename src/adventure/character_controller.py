from __future__ import annotations

import random
from abc import abstractmethod
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, Mapping, Optional, Type, TypeAlias

import pygame as pg
from bidict import bidict
from pygame.event import Event
from transitions import EventData, Machine, State, core
from typing_extensions import override

from ..sprites import Animation
from . import keybind
from .blueprint import StateBlueprint
from .entity import MovingEntity
from .shared import Controller, Direction

UnitVector: TypeAlias = Literal[-1, 0, 1]

CoordDirTranslator: bidict[tuple[UnitVector,
                                 UnitVector],
                           str] = bidict({(0, 1): "down",
                                          (1, 0): "right",
                                          (0, -1): "up",
                                          (-1, 0): "left",
                                          (-1, 1): "downleft",
                                          (1, -1): "upright",
                                          (1, 1): "downright",
                                          (-1, -1): "upleft",
                                          (0, 0): "",
                                          })


class AnimationController(Controller):

    _animation: Animation
    _last_state: str

    def __init__(self, entity: MovingEntity) -> None:
        self._entity = entity
        state = self._get_state()
        self._load_state(state)

    def update(self, dt: float) -> None:
        state = self._get_state()
        if state != self._last_state:
            self._load_state(state)
        else:
            self._animation.update(dt)

        face_direction = self._entity.face_direction
        self._animation.state = Direction(face_direction)
        self._entity.image = self._animation.get_image()

    def _get_state(self) -> str:
        return self._entity.state

    def _load_state(self, state: str) -> None:
        self._animation = self._entity.animations[state]
        self._animation.current_frame = 0
        self._last_state = state


class MovementState(State):

    def __init__(self, name: str | Enum, machine: MovementController, *args: Any, **kwargs: Any) -> None:
        self._machine = machine
        on_enter = kwargs.get("on_enter", None)
        on_exit = kwargs.get("on_exit", None)
        super().__init__(name, on_enter, on_exit)

    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError(type(self))

    @abstractmethod
    def process_collision(self, dt: float) -> None:
        raise NotImplementedError(type(self))


class MovementController(Machine, Controller):

    transitions: list[list[str | list[str]] | dict[str, str | list[str]]]

    def __init__(self, model: MovingEntity, state_table: Mapping[int, StateBlueprint], initial: str | None = None) -> None:
        states = list(dict(table) for table in state_table.values())
        super().__init__(states=states, transitions=self.transitions, initial=initial,
                         auto_transitions=False, model_attribute="state", send_event=True)
        self.add_model(model)

    @override
    def add_model(self, model: list[object] | object, initial: str | Enum | State | None = None) -> None:
        models = core.listify(model)

        if initial is None:
            if self.initial is None:
                raise ValueError(
                    "No initial state configured for machine, must specify when adding model.")
            initial = self.initial

        for mod in models:
            if mod is self.self_literal:
                for trigger in self.events:
                    self._add_trigger_to_model(trigger, self)

                for state in self.states.values():
                    self._add_model_to_state(state, self)

                self._checked_assignment(
                    self, "trigger", partial(self._get_trigger, self))

                self.set_state(initial, model=self)

                return

            if mod not in self.models:
                self.set_state(initial, model=mod)
                self.models.append(mod)

    @override
    def set_state(self, state: str | Enum | State, model: Optional[object] = None) -> None:
        """Change model state when own state is changed."""
        super().set_state(state, model)
        assert model != self.model
        super().set_state(state, self.model)

    def process_collision(self, dt: float) -> None:
        self.get_model_state(self.model).process_collision(dt)

    def update(self, dt: float) -> None:
        self.get_model_state(self.model).update(dt)

    def _move_model_to_last_stable_ground_event(self, event: EventData) -> None:
        dt: float = event.kwargs["dt"]
        self.model.to_last_stable_ground(dt)

    def _set_model_face_direction_event(self, event: EventData) -> None:
        x: UnitVector = event.kwargs.get("x", 0)
        y:  UnitVector = event.kwargs.get("y", 0)

        direction = CoordDirTranslator.get((x, y), "")

        if direction == "":
            return

        self.model.face_direction = Direction(direction)

    def _set_model_unit_vectors_event(self, event: EventData) -> None:
        x: UnitVector = event.kwargs.get('x', 0)
        y: UnitVector = event.kwargs.get('y', 0)

        self.model.velocity[0] = x * self.model.movement_speed
        self.model.velocity[1] = y * self.model.movement_speed

    @override
    def _create_state(self, name: str, default: Type[MovementState], *args: object, **kwargs: object) -> MovementState:
        cls = _get_state_cls(name, default)
        return cls(name=name, machine=self, *args, **kwargs)

    if TYPE_CHECKING:
        @property
        def model(self) -> MovingEntity: ...
        def get_model_state(self, model: object) -> MovementState: ...
        def trigger(self, _: str, **kwargs: object) -> None: ...


class HeroMovementState(MovementState):

    def process_collision(self, dt: float) -> None:
        self._machine.trigger("retreat", dt=dt)

    def update(self, dt: float) -> None:
        pass

    def _get_direction_from_keypress(self) -> tuple[UnitVector, UnitVector]:
        pressed = pg.key.get_pressed()
        x: UnitVector = 0
        y: UnitVector = 0

        if any(pressed[key] for key in keybind.UP):
            y = -1
        elif any(pressed[key] for key in keybind.DOWN):
            y = 1

        if any(pressed[key] for key in keybind.LEFT):
            x = -1
        elif any(pressed[key] for key in keybind.RIGHT):
            x = 1

        return x, y


class IdleState(HeroMovementState):

    def update(self, dt: float) -> None:
        super().update(dt)
        x, y = self._get_direction_from_keypress()
        if x or y:
            self._machine.trigger("walk", x=x, y=y)


class WalkingState(HeroMovementState):

    def __init__(self, name: str | Enum, machine: MovementController, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, machine, *args, **kwargs)
        self._x: UnitVector = 0
        self._y: UnitVector = 0

    def update(self, dt: float) -> None:
        super().update(dt)
        x, y = self._get_direction_from_keypress()

        if not x and not y:
            # A temporary hack to resolve possible collisions before getting into Idle state.
            self._machine.trigger("retreat", dt=dt)
            self._x = x
            self._y = y
            self._machine.trigger("stop")
        else:
            if not (x == self._x and y == self._y):
                self._x = x
                self._y = y
                self._machine.trigger("walk", x=x, y=y)


class ImmobileState(HeroMovementState):

    def update(self, dt: float) -> None:
        super().update(dt)
        x, y = self._get_direction_from_keypress()
        if x or y:
            self._machine.trigger("look", x=x, y=y)


class ChattingState(HeroMovementState):

    ...


class HeroMovementController(MovementController):

    transitions = [
        {"trigger": "walk", "source": ["idle", "walking"], "dest": "walking", "before": [
            "_set_model_unit_vectors_event", "_set_model_face_direction_event"]},

        {"trigger": "stop", "source": ["idle", "walking"], "dest": "idle", "before": [
            "_set_model_unit_vectors_event",]},

        {"trigger": "retreat", "source": "*", "dest": "=", "before": [
        ], "after": ["_move_model_to_last_stable_ground_event"]},

        {"trigger": "look", "source": "*", "dest": "=", "before": [],
            "after": ["_set_model_face_direction_event"]},

        {"trigger": "immobilize", "source": "*", "dest": "immobile"},


        {"trigger": "mobilize", "source": "immobile", "dest": "idle"},
        {"trigger": "enter_conversation", "source": "*", "dest": "chatting"},
        {"trigger": "exit_conversation", "source": "chatting", "dest": "idle"},

    ]

    def _create_state(self, name: str, *args: object, **kwargs: object) -> HeroMovementState:
        default = HeroMovementState
        return super()._create_state(name, default, *args, **kwargs)


class NPCMovementState(MovementState):

    def process_collision(self, dt: float) -> None:
        self._machine.trigger("retreat", dt=dt)

    def reset(self) -> None:
        raise NotImplementedError(type(self), self.name)

    def update(self, dt: float) -> None:
        pass


class NPCIdleState(NPCMovementState):

    def __init__(self, name: str | Enum, machine: NPCMovementController, *args: Any, **kwargs: Any) -> None:
        self._duration = kwargs.get("duration", None)
        self._timer = self._duration
        super().__init__(name, machine, *args, **kwargs)

    def update(self, dt: float) -> None:
        if self._timer is None:
            return
        self._timer -= dt
        if self._timer <= 0:
            self._machine.trigger("stop_idling")

    def reset(self) -> None:
        self._timer = self._duration


class NPCPlanningState(NPCMovementState):

    def __init__(self, name: str | Enum, machine: NPCMovementController, *args: Any, **kwargs: Any) -> None:
        self._duration = kwargs["duration"]
        self._duration_after_block = kwargs["duration_after_block"]
        self._timer = self._duration
        self._blocked: set[Direction] = set()
        super().__init__(name, machine, *args, **kwargs)

    def update(self, dt: float) -> None:
        self._timer -= dt

        if self._timer > 0:
            return

        available = set(Direction).difference(self._blocked)

        if not available:
            self._machine.trigger("find_oneself_stuck")
            return

        direction = random.choice(tuple(available))
        self._blocked.add(direction)
        x, y = CoordDirTranslator.inv[direction.value]
        self._machine.trigger("wander", x=x, y=y)

    def reset(self) -> None:
        self._timer = self._duration
        self._blocked = set()

    def soft_reset(self) -> None:
        self._timer = self._duration_after_block


class NPCWanderingState(NPCMovementState):

    def __init__(self, name: str | Enum, machine: NPCMovementController, *args: Any, **kwargs: Any) -> None:
        self._duration = kwargs["duration"]
        self._timer = self._duration
        self._has_moved = False
        super().__init__(name, machine, *args, **kwargs)

    def process_collision(self, dt: float) -> None:
        super().process_collision(dt)

        if self._has_moved:
            self._machine.trigger("stop")
        else:
            self._machine.trigger("change_plans")

    def reset(self) -> None:
        self._timer = self._duration
        self._has_moved = False

    def update(self, dt: float) -> None:
        self._timer -= dt

        if not self._has_moved and self._duration > self._timer + dt:
            self._has_moved = True

        if self._timer <= 0:
            self._machine.trigger("stop")


class NPCChattingState(NPCMovementState):

    ...


class NPCMovementController(MovementController):

    transitions = [
        {"trigger": "stop_idling", "source": "npc_idle", "dest": "npc_planning",
            "before": [], "after": ["_reset_current_state_event"]},

        {"trigger": "wander", "source": ["npc_planning", "npc_idle"], "dest": "npc_wandering", "before": [
            "_set_model_unit_vectors_event", "_set_model_face_direction_event"], "after": ["_reset_current_state_event"]},

        {"trigger": "stop", "source": ["npc_idle", "npc_wandering"], "dest":"npc_idle", "before": [
            "_set_model_unit_vectors_event"]},

        {"trigger": "retreat", "source": "*", "dest": "npc_idle", "before": [
        ], "after":["_move_model_to_last_stable_ground_event", "stop"]},

        {"trigger": "look", "source": "*", "dest": "=", "before": [],
            "after":["_set_model_face_direction_event"]},

        {"trigger": "change_plans", "source": ["npc_idle", "npc_wandering"], "dest": "npc_planning",
            "before": [], "after": ["_soft_reset_current_state_event"]},

        {"trigger": "enter_conversation", "source": "*", "dest": "npc_chatting",
            "before": [], "after": []},

        {"trigger": "exit_conversation", "source": "npc_chatting", "dest": "npc_idle",
            "before": [], "after": []},
    ]

    def _reset_current_state_event(self, event: EventData) -> None:
        self.get_model_state(self.model).reset()

    def _soft_reset_current_state_event(self, event: EventData) -> None:
        state = self.get_model_state(self.model)
        assert isinstance(state, NPCPlanningState)
        state.soft_reset()

    def _create_state(self, name: str, *args: object, **kwargs: object) -> NPCMovementState:
        default = NPCMovementState
        return super()._create_state(name, default, *args, **kwargs)


class MovementStateType(Enum):

    IDLE = IdleState
    WALKING = WalkingState
    IMMOBILE = ImmobileState
    CHATTING = ChattingState
    NPC_IDLE = NPCIdleState
    NPC_PLANNING = NPCPlanningState
    NPC_WANDERING = NPCWanderingState
    NPC_CHATTING = NPCChattingState


class MovementControllerType(Enum):

    NPC = NPCMovementController
    HERO = HeroMovementController


def _get_state_cls(state: str, default: Type[MovementState]) -> Type[MovementState]:
    try:
        return MovementStateType[state.upper()].value
    except KeyError:
        return default
