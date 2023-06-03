from __future__ import annotations

from enum import Enum
from typing import Final, Literal, TypeAlias, assert_never, cast, get_args


class SourceMark(Enum):

    CURSE = "Curse"
    BLESS = "Bless"
    DISEASE = "Disease"

    MENTAL = "Mental"

    ILLUSIONS = "Illusions"

    TIME = "Time"
    PERMANENT = "Permanent"


class StatusToken:

    def __init__(self, text: str) -> None:
        self.text = text


class Status:

    # Status depends on each mark from the list of marks. Once any mark
    # is removed, the status is considered expired.

    def __init__(self,
                 description: str,
                 marks: list[SourceMark] | None = None,
                 duration: int | None = None,
                 ) -> None:

        if not marks and not duration:
            raise ValueError(
                "The status lacks both marks and duration and thus cannot expire."
                "Pass the SourceMark.PERMANENT explicitly if you want to create a permanent status.")

        self._marks = marks if marks else [SourceMark.TIME]
        self._description = description
        self._duration = duration
        self._token: Final = StatusToken("self._description")
        self._expired = False

    def __str__(self) -> str:
        return self._description

    @property
    def description(self) -> str:
        return self._description

    @property
    def duration(self) -> int | None:
        return self._duration

    @duration.setter
    def duration(self, new_value: int | None) -> None:
        self._duration = new_value

    @property
    def marks(self) -> tuple[SourceMark, ...]:
        return tuple(self._marks)

    @property
    def token(self) -> StatusToken:
        return self._token

    def end_turn(self) -> None:
        if self._duration is None:
            return

        self._duration -= 1

        if self._duration <= 0:
            self._expired = True

    def is_expired(self) -> bool:
        return self._expired

    def remove_mark(self, mark: SourceMark) -> None:
        try:
            self._marks.remove(mark)
        except ValueError:
            return
        else:
            self._expired = True


class OverrideBehaviour(Enum):

    FORCE_OVERRIDE = 1
    OVERRIDE = 2
    PICK_BY_PRIORITY = 3
    PICK_BY_DURATION = 4
    ALWAYS_PASS = 5


Priority: TypeAlias = Literal[0, 1, 2, 3, 4, 5]
PRIORITY_VALUES: tuple[Priority, ...] = get_args(Priority)


class UniqueStatus(Status):

    def __init__(self,
                 description: str,
                 unique_mark: SourceMark,
                 override_behaviour: OverrideBehaviour,
                 marks: list[SourceMark] | None = None,
                 duration: int | None = None,
                 priority: Priority | None = None,
                 overridable: bool = True,
                 ) -> None:

        if marks is None:
            marks = [unique_mark]
        elif not unique_mark in marks:
            marks.append(unique_mark)

        super().__init__(description, marks, duration)

        self._unique_mark = unique_mark
        self._override_behaviour = override_behaviour

        assert self._override_behaviour.value in PRIORITY_VALUES, (
            "Inappropriate override behaviour value, expected to be in"
            f"{str(PRIORITY_VALUES)}, but became {self._override_behaviour.value}.")
        self._priority: Priority = priority if priority is not None else self._override_behaviour.value

        self._overridable = overridable

    @property
    def overridable(self) -> bool:
        return self._overridable

    @property
    def override_behavour(self) -> OverrideBehaviour:
        return self._override_behaviour

    @property
    def priority(self) -> Priority:
        return self._priority

    @property
    def unique_mark(self) -> SourceMark:
        return self._unique_mark


class StatusBar:

    def __init__(self) -> None:
        self._common: list[Status] = []
        self._unique: dict[SourceMark, UniqueStatus] = {}
        self._expired: list[Status] = []

    @property
    def common(self) -> tuple[Status, ...]:
        return tuple(self._common)

    @property
    def expired(self) -> tuple[Status, ...]:
        return tuple(self._expired)

    @property
    def unique(self) -> tuple[UniqueStatus, ...]:
        return tuple(self._unique.values())

    def add_status(self, status: Status) -> None:
        if isinstance(status, UniqueStatus):
            self._add_unique_status(status)
        else:
            self._common.append(status)

    def clean_expired(self) -> None:
        self._expired = []

    def end_turn(self) -> None:
        for status in self._common:
            status.end_turn()

        for status in self._unique.values():
            status.end_turn()

        self._refresh()

    def pop_expired(self) -> tuple[Status, ...]:
        expired = self.expired
        self.clean_expired()
        return expired

    def remove_mark(self, mark: SourceMark) -> None:
        for status in self._common:
            status.remove_mark(mark)

        for status in self._unique.values():
            status.remove_mark(mark)

        self._refresh()

    def _add_unique_status(self, status: UniqueStatus) -> None:
        mark = status.unique_mark

        if mark not in self._unique:
            self._unique[mark] = status
            return

        self._unique[mark] = self._find_winner(
            self._unique[mark], status, status.override_behavour)

    @staticmethod
    def _find_winner(old: UniqueStatus, new: UniqueStatus, behaviour: OverrideBehaviour) -> UniqueStatus:
        # Forced override from new ignores if old is not overridable.
        if behaviour is OverrideBehaviour.FORCE_OVERRIDE:
            return new

        # Non-overridable old ignores non-forced override from new.
        if not old.overridable:
            return old

        if behaviour is OverrideBehaviour.OVERRIDE:
            return new

        if behaviour is OverrideBehaviour.ALWAYS_PASS:
            return old

        if behaviour is OverrideBehaviour.PICK_BY_PRIORITY:
            if old.priority == new.priority:
                # Even priority, proceed to the next behaviour (pick by duration).
                behaviour = OverrideBehaviour(behaviour.value + 1)
                return StatusBar._find_winner(old, new, behaviour)

            return min(old, new, key=lambda status: status.priority)

        if behaviour is OverrideBehaviour.PICK_BY_DURATION:
            if old.duration == new.duration:
                # Even duration, proceed to the next behaviour (pass).
                behaviour = OverrideBehaviour(behaviour.value + 1)
                return StatusBar._find_winner(old, new, behaviour)

            if old.duration is None:
                return old
            if new.duration is None:
                return new

            # None values are excluded via the lines just above.
            return max(old, new, key=lambda status: cast(int, status.duration))

        assert_never(behaviour)

    def _refresh(self) -> None:
        expired, common = [], []
        for status in self._common:
            expired.append(status) if status.is_expired(
            ) else common.append(status)

        unique = []
        for status in self._unique.values():
            expired.append(status) if status.is_expired(
            ) else unique.append(status)

        self._expired.extend(expired)
        self._common = common
        self._unique = {status.unique_mark: status for status in unique}
