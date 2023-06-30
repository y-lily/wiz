from __future__ import annotations

import random
from abc import abstractmethod
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Literal, Mapping, Type, TypeAlias

import pygame as pg
from bidict import bidict
from transitions import EventData, Machine, State, core
from typing_extensions import override

# TODO:
# import keybind
# from shared import Controller, Direction, pair
# from sprites import Animation
from src import keybind
from src.shared import Controller, Direction, pair
from src.sprites import Animation

from .blueprint import StateBlueprint
from .entity import MovingEntity

UnitVector: TypeAlias = Literal[-1, 0, 1]
Coordinate: TypeAlias = pair[UnitVector]

_COORD_DIR_TRANSLATOR: bidict[Coordinate,
                              Direction | None] = bidict({(0, 1): Direction.DOWN,
                                                          (1, 0): Direction.RIGHT,
                                                          (0, -1): Direction.UP,
                                                          (-1, 0): Direction.LEFT,
                                                          (-1, 1): Direction.DOWNLEFT,
                                                          (1, -1): Direction.UPRIGHT,
                                                          (1, 1): Direction.DOWNRIGHT,
                                                          (-1, -1): Direction.UPLEFT,
                                                          (0, 0): None,
                                                          })


def coordinate_to_direction(coordinate: Coordinate) -> Direction | None:
    return _COORD_DIR_TRANSLATOR.get(coordinate, None)


def direction_to_coordinate(direction: Direction) -> Coordinate:
    return _COORD_DIR_TRANSLATOR.inv.get(direction)


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


class MovementController(Machine, Controller):

    if TYPE_CHECKING:
        @property
        def model(self) -> MovingEntity: ...
        def get_model_state(self, model: object) -> MovementState: ...
        def trigger(self, _: str, **kwargs: object) -> None: ...

    transitions: list[list[str | list[str]] | dict[str, str | list[str]]]

    def __init__(self,
                 model: MovingEntity,
                 state_table: Mapping[int, StateBlueprint],
                 initial: str | Enum | State | None = None,
                 ) -> None:

        states = list(dict(table) for table in state_table.values())

        # Detect if it's been accidentally renamed.
        assert hasattr(model, "state")
        super().__init__(states=states,
                         transitions=self.transitions,
                         initial=initial,
                         auto_transitions=False,
                         model_attribute="state",
                         send_event=True,
                         )

        self.add_model(model)

    @override
    def add_model(self,
                  model: list[object] | object,
                  initial: str | Enum | State | None = None,
                  ) -> None:

        models = core.listify(model)

        initial = initial if initial is not None else self.initial
        if initial is None:
            raise ValueError("No initial state has been configured for the machine, \
                             must be specified when adding a model.")

        for mod in models:
            if mod is self.self_literal:
                for trigger in self.events:
                    self._add_trigger_to_model(trigger, self)
                for state in self.states.values():
                    self._add_model_to_state(state, self)
                self._checked_assignment(self,
                                         "trigger",
                                         partial(self._get_trigger, self))
                self.set_state(initial, model=self)
                return

            if mod not in self.models:
                self.set_state(initial, model=mod)
                self.models.append(mod)

    @override
    def set_state(self,
                  new_state: str | Enum | State,
                  model: object | None = None,
                  ) -> None:

        # Ensure the model's state changes on each call.
        super().set_state(new_state, model)
        assert model != self.model
        super().set_state(new_state, self.model)

    @override
    def update(self, dt: float) -> None:
        self.get_model_state(self.model).update(dt)

    @override
    def _create_state(self,
                      name: str,
                      default: Type[MovementState],
                      *args: object,
                      **kwargs: object,
                      ) -> MovementState:

        cls = _get_state_cls(name, default)
        return cls(name=name, machine=self, *args, **kwargs)

    def handle_collision(self, dt: float) -> None:
        self.get_model_state(self.model).handle_collision(dt)

    def move_to_last_stable_ground(self, event: EventData) -> None:
        dt: float = event.kwargs["dt"]
        self.model.to_last_stable_ground(dt)

    def set_face_direction(self, event: EventData) -> None:
        x: UnitVector = event.kwargs.get("x", 0)
        y: UnitVector = event.kwargs.get("y", 0)

        if (direction := coordinate_to_direction((x, y))) is not None:
            self.model.face_direction = direction

    def set_unit_vectors(self, event: EventData) -> None:
        x: UnitVector = event.kwargs.get("x", 0)
        y: UnitVector = event.kwargs.get("y", 0)

        self.model.velocity[0] = x * self.model.movement_speed
        self.model.velocity[1] = y * self.model.movement_speed


class HeroMovementController(MovementController):

    transitions = [
        {"trigger": "walk",
         "source": ["idle", "walking",],
         "dest": "walking",
         "before": ["set_unit_vectors", "set_face_direction",]},

        {"trigger": "stop",
         "source": ["idle", "walking",],
         "dest": "idle",
         "before": ["set_unit_vectors",]},

        {"trigger": "retreat",
         "source": "*",
         "dest": "=",
         "before": [],
         "after": ["move_to_last_stable_ground",]},

        {"trigger": "look",
         "source": "*",
         "dest": "=",
         "before": [],
         "after": ["set_face_direction",]},

        {"trigger": "immobilize",
         "source": "*",
         "dest": "immobile"},

        {"trigger": "mobilize",
         "source": "immobile",
         "dest": "idle"},

        {"trigger": "enter_conversation",
         "source": "*",
         "dest": "chatting",
         "before": ["set_unit_vectors",]},

        {"trigger": "exit_conversation",
            "source": "chatting",
            "dest": "idle"},
    ]

    @override
    def _create_state(self,
                      name: str,
                      *args: object,
                      **kwargs: object,
                      ) -> MovementState:

        default = HeroMovementState
        return super()._create_state(name, default, *args, **kwargs)


class MovementState(State):

    def __init__(self,
                 name: str | Enum,
                 machine: MovementController,
                 *_: object,
                 **kwargs: object,
                 ) -> None:

        self._machine = machine
        super().__init__(name,
                         on_enter=kwargs.get("on_enter", None),
                         on_exit=kwargs.get("on_exit", None))

    @abstractmethod
    def handle_collision(self, dt: float) -> None:
        raise NotImplementedError(type(self))

    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError(type(self))


class HeroMovementState(MovementState):

    @override
    def handle_collision(self, dt: float) -> None:
        self._machine.trigger("retreat", dt=dt)

    @override
    def update(self, dt: float) -> None:
        pass


class IdleState(HeroMovementState):

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        x, y = get_coordinate_from_pressed()
        if x or y:
            self._machine.trigger("walk", x=x, y=y)


class WalkingState(HeroMovementState):

    def __init__(self,
                 name: str | Enum,
                 machine: MovementController,
                 *args: object,
                 **kwargs: object,
                 ) -> None:

        super().__init__(name, machine, *args, **kwargs)
        self._x: UnitVector = 0
        self._y: UnitVector = 0

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        x, y = get_coordinate_from_pressed()

        if not x and not y:
            # A hack to handle possible collisions before entering the Idle state
            # (which does not know how to deal with collisions).
            self._machine.trigger("retreat", dt=dt)
            self._x = x
            self._y = y
            self._machine.trigger("stop")

        elif not (x == self._x and y == self._y):
            self._x = x
            self._y = y
            self._machine.trigger("walk", x=x, y=y)


class ImmobileState(HeroMovementState):

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        x, y = get_coordinate_from_pressed()
        if x or y:
            self._machine.trigger("look", x=x, y=y)


class ChattingState(HeroMovementState):

    ...


class NPCMovementController(MovementController):

    transitions = [
        {"trigger": "stop_idling",
         "source": "npc_idle",
         "dest": "npc_planning",
         "before": [],
         "after": ["reset_state",]},

        {"trigger": "wander",
         "source": ["npc_planning", "npc_idle",],
         "dest": "npc_wandering",
         "before": ["set_unit_vectors", "set_face_direction",],
         "after": ["reset_state",]},

        {"trigger": "stop",
         "source": ["npc_idle", "npc_wandering",],
         "dest": "npc_idle",
         "before": ["set_unit_vectors",]},

        {"trigger": "retreat",
         "source": "*",
         "dest": "npc_idle",
         "before": [],
         "after": ["move_to_last_stable_ground", "stop",]},

        {"trigger": "look",
         "source": "*",
         "dest": "=",
         "before": [],
         "after": ["set_face_direction",]},

        {"trigger": "change_plans",
         "source": ["npc_idle", "npc_wandering",],
         "dest": "npc_planning",
         "before": [],
         "after": ["soft_reset_state",]},

        {"trigger": "enter_conversation",
         "source": "*",
         "dest": "npc_chatting",
         "before": ["set_unit_vectors",]},

        {"trigger": "exit_conversation",
            "source": "npc_chatting",
            "dest": "npc_idle"},
    ]

    def reset_state(self, event: EventData) -> None:
        self.get_model_state(self.model).reset()

    def soft_reset_state(self, event: EventData) -> None:
        state = self.get_model_state(self.model)
        assert isinstance(state, NPCPlanningState)
        state.soft_reset()

    @override
    def _create_state(self,
                      name: str,
                      *args: object,
                      **kwargs: object,
                      ) -> None:

        default = NPCMovementState
        return super()._create_state(name, default, *args, **kwargs)


class NPCMovementState(MovementState):

    @override
    def handle_collision(self, dt: float) -> None:
        self._machine.trigger("retreat", dt=dt)

    @override
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError(type(self), self.name)


class NPCIdleState(NPCMovementState):

    def __init__(self,
                 name: str | Enum,
                 machine: NPCMovementController,
                 *args: object,
                 **kwargs: object,
                 ) -> None:

        super().__init__(name, machine, *args, **kwargs)
        self._duration: float | None = kwargs.get("duration", None)
        self._timer = self._duration

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        if self._timer is None:
            return

        self._timer -= dt

        if self._timer <= 0:
            self._machine.trigger("stop_idling")

    @override
    def reset(self) -> None:
        self._timer = self._duration


class NPCPlanningState(NPCMovementState):

    def __init__(self,
                 name: str | Enum,
                 machine: NPCMovementController,
                 *args: object,
                 **kwargs: object,
                 ) -> None:

        super().__init__(name, machine, *args, **kwargs)
        self._duration: float = kwargs["duration"]
        self._duration_after_block: float = kwargs["duration_after_block"]
        self._timer = self._duration
        self._blocked: set[Direction] = set()

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        self._timer -= dt

        if self._timer > 0:
            return

        available = set(Direction).difference(self._blocked)

        if not available:
            self._machine.trigger("find_oneself_stuck")
            return

        direction = random.choice(tuple(available))
        self._blocked.add(direction)
        x, y = direction_to_coordinate(direction)
        self._machine.trigger("wander", x=x, y=y)

    @override
    def reset(self) -> None:
        self._timer = self._duration
        self._blocked.clear()

    def soft_reset(self) -> None:
        self._timer = self._duration_after_block


class NPCWanderingState(NPCMovementState):

    def __init__(self,
                 name: str | Enum,
                 machine: NPCMovementController,
                 *args: object,
                 **kwargs: object,
                 ) -> None:

        super().__init__(name, machine, *args, **kwargs)
        self._duration: float = kwargs["duration"]
        self._timer = self._duration
        self._has_moved = False

    @override
    def handle_collision(self, dt: float) -> None:
        super().handle_collision(dt)

        if self._has_moved:
            self._machine.trigger("stop")
        else:
            self._machine.trigger("change_plans")

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        self._timer -= dt

        if not self._has_moved and self._duration > self._timer + dt:
            self._has_moved = True

        if self._timer <= 0:
            self._machine.trigger("stop")

    @override
    def reset(self) -> None:
        self._timer = self._duration
        self._has_moved = False


class NPCChattingState(NPCMovementState):

    ...


class MovementStateType(Enum):

    IDLE = IdleState
    WALKING = WalkingState
    IMMOBILE = ImmobileState
    CHATTING = ChattingState
    NPC_IDLE = NPCIdleState
    NPC_PLANNING = NPCPlanningState
    NPC_WANDERING = NPCWanderingState
    NPC_CHATTING = NPCChattingState


class CharacterType(Enum):

    NPC = NPCMovementController
    HERO = HeroMovementController


def _get_state_cls(state: str, default: Type[MovementState]) -> Type[MovementState]:
    try:
        return MovementStateType[state.upper()].value
    except KeyError:
        return default


def get_coordinate_from_pressed() -> Coordinate:
    pressed = pg.key.get_pressed()
    x: UnitVector = 0
    y: UnitVector = 0

    if any(pressed[key] for key in keybind.UP):
        y -= 1
    if any(pressed[key] for key in keybind.DOWN):
        y += 1

    if any(pressed[key] for key in keybind.LEFT):
        x -= 1
    if any(pressed[key] for key in keybind.RIGHT):
        x += 1

    return x, y
