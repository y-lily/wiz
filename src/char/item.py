from abc import ABC
from typing import Any, Iterator, Mapping, Type, TypeVar, cast


class ItemComponent(ABC):

    ...


class ItemCost(ItemComponent):

    ...


class Cost(ItemComponent):

    ...


class Weight(ItemComponent):

    ...


class ItemProperty(ItemComponent):

    ...


class ThrowableProperty(ItemProperty):

    # effects: ???
    # rules: ???

    ...


class ConsumableProperty(ItemProperty):

    # effects: ???

    ...


class Quantity(ItemComponent):

    ...


CT = TypeVar("CT")
C = TypeVar("C", bound=ItemComponent)


class ComponentBlock(Mapping[CT, C]):

    def __init__(self, components: dict[CT, C]) -> None:
        self._components: dict[CT, C] = components

    def __getitem__(self, __key: CT) -> C:
        return self._components.__getitem__(__key)

    def __iter__(self) -> Iterator[CT]:
        return self._components.__iter__()


CB = TypeVar("CB", bound=ComponentBlock[Any, Any])


class ComponentSheet:

    def __init__(self, *blocks: ComponentBlock[Any, Any]) -> None:
        self._blocks = {type(block): block for block in blocks}

    def __iter__(self) -> Iterator[ComponentBlock[Any, Any]]:
        return self._blocks.values().__iter__()

    def add(self, block: Type[CB]) -> CB:
        # The keys are always supposed to be the types of values.
        return cast(CB, self._blocks[block])

    def remove(self, block: Type[CB]) -> None:
        self._blocks.pop(block)


# Items should have unique tokens with them so you can track the changes they've made within the status bar.


# class Animal:

#     def feed(self, food: str) -> None:
#         print(f"{self.__class__} gets {food}")


# class Fox(Animal):

#     def feed(self, food: str, optional: str | None = None) -> None:
#         super().feed(food)
#         if optional:
#             print(f"optional {optional}")


# if __name__ == "__main__":
#     from functools import partial, partialmethod

#     bear = Animal()
#     fox = Fox()
#     zoo: dict[int, Animal] = {1: bear, 2: fox}

#     provision = {1: ["meat"], 2: ("fish", "chicken")}

#     # provision = {1: {"food": "meat"}, 2: {
#     #     "food": "fish", "optional": "chicken"}}

#     for n, food_args in provision.items():
#         # if n == 1:
#         #     continue
#         # f = partial(zoo[n].feed)
#         # f(*food_args)
#         # f = partial(zoo[n].feed)
#         # f(*food_args)
#         # print(*food_args)
#         zoo[n].feed(*food_args)
