from __future__ import annotations

from pathlib import Path

from lupa import LuaRuntime

from ..sprites import SpriteKeeper
from .animation_builder import AnimationBuilder
from .blueprint import CharacterBlueprint
from .character import Character
from .character_controller import AnimationController, MovementControllerType
from .entity import MovingEntity


class CharacterLoader:

    def __init__(self, sprite_keeper: SpriteKeeper) -> None:
        self._builder = CharacterBuilder(sprite_keeper)

    def load(self, char_path: Path, char_type: str = "NPC") -> Character:
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(char_path, "r") as file:
            char_def: CharacterBlueprint = lua.execute(file.read())
        return self._builder.build(char_def=char_def, char_type=char_type)


class CharacterBuilder:

    def __init__(self, sprite_keeper: SpriteKeeper) -> None:
        self._animation_builder = AnimationBuilder(sprite_keeper)

    def build(self, char_def: CharacterBlueprint, char_type: str = "NPC") -> Character:
        entity_def = char_def.entity
        animations = self._animation_builder.build(entity_def)

        if char_def.movement_speed is not None:
            speed = char_def.movement_speed
        else:
            speed = entity_def.movement_speed

        entity = MovingEntity(animations=animations,
                              movement_speed=speed,
                              state=char_def.state,
                              face_direction=entity_def.face_direction,
                              frame=entity_def.frame,
                              position=char_def.position,
                              )

        char = Character(name=char_def.name,
                         entity=entity,
                         trigger=char_def.trigger)

        return _setup_char(char, char_def, char_type)


def _setup_char(char: Character, char_def: CharacterBlueprint, char_type: str) -> Character:
    cls = MovementControllerType[char_type.upper()].value
    char.add_controller(AnimationController(char.entity))
    char.add_movement_controller(cls(
        char.entity, state_table=char_def.defined_states, initial=char_def.state))
    return char
