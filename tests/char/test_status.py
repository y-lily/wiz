import pytest
from pytest_lazyfixture import lazy_fixture

from src.char.status import (
    OverrideBehaviour,
    SourceMark,
    Status,
    StatusBar,
    UniqueStatus,
)


class TestStatus:

    @pytest.fixture
    def mental_mark(self) -> SourceMark:
        return SourceMark.MENTAL

    @pytest.fixture
    def illusions_mark(self) -> SourceMark:
        return SourceMark.ILLUSIONS

    @pytest.fixture
    def confusion(self, mental_mark: SourceMark, illusions_mark: SourceMark) -> Status:
        return Status("is confused", [mental_mark, illusions_mark], 1)

    def test_status_is_not_expired_on_creation(self, confusion: Status) -> None:
        assert not confusion.is_expired()

    @pytest.mark.parametrize('mark', (lazy_fixture('mental_mark'), lazy_fixture('illusions_mark')))
    def test_status_expires_if_any_mark_is_removed(self, confusion: Status, mark: SourceMark) -> None:
        confusion.remove_mark(mark)
        assert confusion.is_expired()

    def test_status_expires_if_time_expires(self, confusion: Status) -> None:
        confusion.end_turn()
        assert confusion.is_expired()

    def test_passing_empty_marks_and_duration_equal_to_none_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = Status(
                "cannot get rid of this status", [], None)

    def test_end_turn_decreases_duration(self) -> None:
        status = Status("", duration=5)
        status.end_turn()

        assert status.duration == 4

    def test_end_turn_does_not_change_duration_if_duration_is_none(self) -> None:
        status = Status("", [SourceMark.BLESS], None)
        status.end_turn()

        assert status.duration is None

    @pytest.mark.parametrize("duration", (4, None))
    def test_end_turn_does_not_make_status_expired_if_duration_does_not_become_zero(self, duration: int | None) -> None:
        status = Status("", [SourceMark.BLESS], duration)
        status.end_turn()

        assert not status.is_expired()

    def test_attempting_to_remove_non_present_mark_does_not_make_status_expired(self, confusion: Status) -> None:
        confusion.remove_mark(SourceMark.BLESS)
        assert not confusion.is_expired()


class TestUniqueStatus:

    @pytest.fixture
    def unique_mark(self) -> SourceMark:
        return SourceMark.MENTAL

    @pytest.mark.parametrize("marks", ([SourceMark.BLESS], [], None))
    def test_marks_will_contain_unique_mark_after_construction(self, marks: list[SourceMark] | None, unique_mark: SourceMark) -> None:
        status = UniqueStatus(
            "", unique_mark, OverrideBehaviour.ALWAYS_PASS, marks=marks)

        assert unique_mark in status.marks

    def test_unique_mark_will_not_be_added_to_marks_if_already_present(self, unique_mark: SourceMark) -> None:
        marks = [unique_mark]
        status = UniqueStatus(
            "", unique_mark, OverrideBehaviour.ALWAYS_PASS, marks=marks)

        assert len(status.marks) == 1


class TestStatusBar:

    @pytest.fixture
    def confusion(self) -> Status:
        return Status("is confused", [SourceMark.ILLUSIONS, SourceMark.MENTAL], duration=1)

    @pytest.fixture
    def unique_curse(self) -> UniqueStatus:
        return UniqueStatus("is cursed", SourceMark.CURSE, OverrideBehaviour.ALWAYS_PASS, duration=1)

    @pytest.fixture
    def status_bar(self) -> StatusBar:
        return StatusBar()

    def test_common_status_is_added_to_common(self, status_bar: StatusBar, confusion: Status) -> None:
        status_bar.add_status(confusion)
        assert confusion in status_bar.common

    def test_unique_status_is_added_to_unique(self, status_bar: StatusBar, unique_curse: UniqueStatus) -> None:
        status_bar.add_status(unique_curse)
        assert unique_curse in status_bar.unique

    @pytest.mark.parametrize("status, mark", [(lazy_fixture('confusion'), SourceMark.MENTAL), (lazy_fixture('unique_curse'), SourceMark.CURSE)])
    def test_removing_status_mark_moves_status_to_expired(self, status_bar: StatusBar, status: Status, mark: SourceMark) -> None:
        status_bar.add_status(status)
        status_bar.remove_mark(mark)

        assert status in status_bar.expired

    @pytest.mark.parametrize("status, mark", [(lazy_fixture('confusion'), SourceMark.MENTAL), (lazy_fixture('unique_curse'), SourceMark.CURSE)])
    def test_removing_status_mark_removes_status_from_statuses(self, status_bar: StatusBar, status: Status, mark: SourceMark) -> None:
        status_bar.add_status(status)
        status_bar.remove_mark(mark)

        assert status not in status_bar.common and status not in status_bar.unique

    @pytest.mark.parametrize("status", (lazy_fixture('confusion'), lazy_fixture('unique_curse')))
    def test_ending_turn_moves_status_to_expired_if_duration_expires(self, status_bar: StatusBar, status: Status) -> None:
        status_bar.add_status(status)
        status_bar.end_turn()

        assert status in status_bar.expired

    @pytest.mark.parametrize("status", (lazy_fixture('confusion'), lazy_fixture('unique_curse')))
    def test_ending_turn_removes_status_from_statuses_if_duration_expires(self, status_bar: StatusBar, status: Status) -> None:
        status_bar.add_status(status)
        status_bar.end_turn()

        assert status not in status_bar.common and status not in status_bar.unique

    @pytest.mark.parametrize("status", (lazy_fixture('confusion'), lazy_fixture('unique_curse')))
    def test_attempting_to_remove_non_present_mark_does_not_move_status_to_expired(self, status_bar: StatusBar, status: Status) -> None:
        status_bar.add_status(status)
        status_bar.remove_mark(SourceMark.BLESS)

        assert status not in status_bar.expired

    @pytest.mark.parametrize("status", (Status("", [], duration=2),
                                        Status(
                                            "", [SourceMark.BLESS], duration=None),
                                        UniqueStatus(
                                            "", SourceMark.BLESS, OverrideBehaviour.ALWAYS_PASS, duration=2),
                                        UniqueStatus("", SourceMark.BLESS, OverrideBehaviour.ALWAYS_PASS, duration=None)))
    def test_ending_turn_does_not_move_status_to_expired_if_duration_does_not_expire(self, status_bar: StatusBar, status: Status) -> None:
        status_bar.add_status(status)
        status_bar.end_turn()

        assert status not in status_bar.expired

    def test_calling_expired_does_not_clean_expired(self, status_bar: StatusBar, confusion: Status) -> None:
        status_bar.add_status(confusion)
        status_bar.end_turn()

        first_call = status_bar.expired
        second_call = status_bar.expired

        assert first_call == second_call

    def test_calling_clean_expired_cleans_expired(self, status_bar: StatusBar, confusion: Status) -> None:
        status_bar.add_status(confusion)
        status_bar.end_turn()
        status_bar.clean_expired()

        assert confusion not in status_bar.expired

    def test_calling_pop_expired_cleans_expired(self, status_bar: StatusBar, confusion: Status) -> None:
        status_bar.add_status(confusion)
        status_bar.end_turn()
        _ = status_bar.pop_expired()

        assert confusion not in status_bar.expired

    @pytest.fixture
    def shared_mark(self) -> SourceMark:
        return SourceMark.DISEASE

    @pytest.fixture
    def non_overridable(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.ALWAYS_PASS, overridable=False)

    def test_forced_override_behaviour_overrides_non_overridable(self, status_bar: StatusBar, non_overridable: UniqueStatus, shared_mark: SourceMark) -> None:
        status_bar.add_status(non_overridable)
        new = UniqueStatus("", shared_mark, OverrideBehaviour.FORCE_OVERRIDE)
        status_bar.add_status(new)

        assert non_overridable not in status_bar.unique and new in status_bar.unique

    @pytest.mark.parametrize("behaviour", (OverrideBehaviour.ALWAYS_PASS, OverrideBehaviour.OVERRIDE, OverrideBehaviour.PICK_BY_DURATION, OverrideBehaviour.PICK_BY_PRIORITY))
    def test_non_overridable_is_not_overriden_by_non_forced_override(self, status_bar: StatusBar, non_overridable: UniqueStatus, shared_mark: SourceMark, behaviour: OverrideBehaviour) -> None:
        status_bar.add_status(non_overridable)
        new = UniqueStatus("", shared_mark, behaviour)
        status_bar.add_status(new)

        assert non_overridable in status_bar.unique and new not in status_bar.unique

    @pytest.fixture
    def shorter_duration(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_DURATION, duration=1)

    @pytest.fixture
    def longer_duration(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_DURATION, duration=2)

    @pytest.mark.parametrize("old, new", [
        (lazy_fixture('shorter_duration'), lazy_fixture('longer_duration')),
        (lazy_fixture('longer_duration'), lazy_fixture('shorter_duration'))
    ])
    def test_pick_by_duration_behaviour_picks_status_with_longer_duration(self, status_bar: StatusBar, old: UniqueStatus, new: UniqueStatus, shorter_duration: UniqueStatus, longer_duration: UniqueStatus) -> None:
        status_bar.add_status(old)
        status_bar.add_status(new)

        assert shorter_duration not in status_bar.unique and longer_duration in status_bar.unique

    @pytest.fixture
    def lower_priority_value(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_PRIORITY, priority=1)

    @pytest.fixture
    def higher_priority_value(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_PRIORITY, priority=2)

    @pytest.mark.parametrize("old, new", [
        (
            lazy_fixture('higher_priority_value'),
            lazy_fixture('lower_priority_value')),
        (
            lazy_fixture('lower_priority_value'),
            lazy_fixture('higher_priority_value'))
    ])
    def test_pick_by_priority_behaviour_picks_status_with_lower_priority_value(self, status_bar: StatusBar, old: UniqueStatus, new: UniqueStatus, higher_priority_value: UniqueStatus, lower_priority_value: UniqueStatus) -> None:
        status_bar.add_status(old)
        status_bar.add_status(new)

        assert higher_priority_value not in status_bar.unique and lower_priority_value in status_bar.unique

    @pytest.fixture
    def even_priority_longer_duration(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_PRIORITY, priority=1, duration=2)

    @pytest.fixture
    def even_priority_shorter_duration(self, shared_mark: SourceMark) -> UniqueStatus:
        return UniqueStatus("", shared_mark, OverrideBehaviour.PICK_BY_PRIORITY, priority=1, duration=1)

    @pytest.mark.parametrize("old, new", [
        (
            lazy_fixture('even_priority_longer_duration'),
            lazy_fixture('even_priority_shorter_duration')),
        (
            lazy_fixture('even_priority_shorter_duration'),
            lazy_fixture('even_priority_longer_duration')
        )
    ])
    def test_pick_by_priority_picks_status_with_longer_duration_if_priorities_are_even(self, status_bar: StatusBar, old: UniqueStatus, new: UniqueStatus, even_priority_shorter_duration: UniqueStatus, even_priority_longer_duration: UniqueStatus) -> None:
        status_bar.add_status(old)
        status_bar.add_status(new)

        assert even_priority_shorter_duration not in status_bar.unique and even_priority_longer_duration in status_bar.unique

    @pytest.mark.parametrize('behaviour', (OverrideBehaviour.PICK_BY_PRIORITY, OverrideBehaviour.PICK_BY_DURATION))
    def test_old_status_is_kept_if_priorities_and_durations_are_even(self, status_bar: StatusBar, shared_mark: SourceMark, behaviour: OverrideBehaviour) -> None:
        old = UniqueStatus("", shared_mark, behaviour,
                           duration=1, priority=1)
        new = UniqueStatus("", shared_mark, behaviour,
                           duration=1, priority=1)

        status_bar.add_status(old)
        status_bar.add_status(new)

        assert old in status_bar.unique and new not in status_bar.unique
