from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum, auto
from typing import Any, Generic, MutableSequence, Protocol, TypeVar, overload

from typing_extensions import SupportsIndex


class Publisher:

    def __init__(self) -> None:
        self._subscribers: set[Subscriber] = set()

    def add_subscriber(self, subscriber: Subscriber) -> None:
        self._subscribers.add(subscriber)

    def remove_subscriber(self, subscriber: Subscriber) -> None:
        self._subscribers.remove(subscriber)

    def send_notification(self, notification: Any = None) -> None:
        for subscriber in self._subscribers:
            subscriber.notify(notification)


T = TypeVar("T")


class ListPublisher(Publisher, MutableSequence[T]):

    def __init__(self, items: Iterable[T] | None = None) -> None:
        super().__init__()
        self._items: list[T] = list(items) if items is not None else list()

    @overload
    def __getitem__(self, key: SupportsIndex, /) -> T: ...
    @overload
    def __getitem__(self, key: slice, /) -> list[T]: ...

    def __getitem__(self, key: SupportsIndex | slice) -> T | list[T]:
        return self._items.__getitem__(key)

    @overload
    def __setitem__(self, key: SupportsIndex, value: T, /) -> None: ...
    @overload
    def __setitem__(self, key: slice, value: Iterable[T], /) -> None: ...

    def __setitem__(self, key: SupportsIndex | slice, value: T | Iterable[T]) -> None:
        self._items.__setitem__(key, value)

        event: ListEvent[T] = ListEvent(
            ListEventType.SETITEM, key=key, value=value)
        self.send_notification(event)

    def __delitem__(self, key: SupportsIndex | slice) -> None:
        self._items.__delitem__(key)

        event: ListEvent[T] = ListEvent(
            ListEventType.DELITEM, key=key)
        self.send_notification(event)

    def __len__(self) -> int:
        return self._items.__len__()

    def append(self, value: T) -> None:
        self._items.append(value)

        event: ListEvent[T] = ListEvent(
            ListEventType.APPEND, value=value)
        self.send_notification(event)

    def remove(self, value: T) -> None:
        self._items.remove(value)

        event: ListEvent[T] = ListEvent(
            ListEventType.REMOVE, value=value)
        self.send_notification(event)

    def clear(self) -> None:
        self._items.clear()

        event: ListEvent[T] = ListEvent(ListEventType.CLEAR)
        self.send_notification(event)

    def extend(self, __iterable: Iterable[T]) -> None:
        self._items.extend(__iterable)

        event: ListEvent[T] = ListEvent(
            ListEventType.EXTEND, value=__iterable)
        self.send_notification(event)

    def insert(self, __index: SupportsIndex, value: T) -> None:
        self._items.insert(__index, value)

        event: ListEvent[T] = ListEvent(
            ListEventType.INSERT, index=__index, value=value)
        self.send_notification(event)


class Subscriber(ABC):

    @abstractmethod
    def notify(self, event: Any) -> None:
        pass


class ListEvent(Generic[T]):

    eventtype: ListEventType
    key: SupportsIndex | slice
    value: T | Iterable[T]
    index: SupportsIndex

    def __init__(self,
                 eventtype: ListEventType,
                 /,
                 key: SupportsIndex | slice | None = None,
                 value: T | Iterable[T] | None = None,
                 index: SupportsIndex | None = None,
                 ) -> None:

        self.eventtype = eventtype
        if key is not None:
            self.key = key
        if value is not None:
            self.value = value
        if index is not None:
            self.index = index


class ListEventType(Enum):

    SETITEM = auto()
    DELITEM = auto()
    APPEND = auto()
    REMOVE = auto()
    CLEAR = auto()
    EXTEND = auto()
    INSERT = auto()
