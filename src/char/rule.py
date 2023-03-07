from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Type, TypedDict


class Context(ABC):
    pass


@dataclass
class AttackContext(Context):

    attacker: object
    defender: object
    attack_info: object


class Rule:

    def __init__()
