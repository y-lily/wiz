from typing import Any

import pytest

from src.ui.observer import ListPublisher, Subscriber


class MockSubscriber(Subscriber):

    def __init__(self) -> None:
        self.notified = False

    def notify(self, event: Any = None) -> None:
        self.notified = True

    def unnotify(self) -> None:
        self.notified = False


class TestObserver:

    @pytest.fixture
    def publisher(self) -> ListPublisher[int]:
        return ListPublisher()

    @pytest.fixture
    def subscriber(self, publisher: ListPublisher[int]) -> MockSubscriber:
        publisher.add_subscriber(sub := MockSubscriber())
        return sub

    def test_append_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        assert subscriber.notified

    def test_remove_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        subscriber.unnotify()
        publisher.remove(1)
        assert subscriber.notified

    def test_clear_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        subscriber.unnotify()
        publisher.clear()
        assert subscriber.notified

    def test_extend_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.extend((1, 2))
        assert subscriber.notified

    def test_insert_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        subscriber.unnotify()
        publisher.insert(0, 3)
        assert subscriber.notified

    def test_getitem_returns_item(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        assert publisher[0] == 1

    def test_getitem_by_slice_returns_list(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        assert publisher[0:2] == [1, 2]

    def test_getitem_does_not_notify(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        subscriber.unnotify()
        _ = publisher[0]
        assert not subscriber.notified

    def test_setitem_sets_item(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher[0] = 2
        assert publisher[0] == 2

    def test_setitem_for_slice_sets_multiple_items(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        publisher[0:2] = (3, 4, 5)
        assert publisher[0:3] == [3, 4, 5]

    def test_delitem_deletes_item(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        del publisher[1]
        assert publisher[:] == [1]

    def test_delitem_for_slice_deletes_multiple_items(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        publisher.append(3)
        del publisher[:2]
        assert publisher[:] == [3]

    def test_delitem_notifies(self, publisher: ListPublisher[int], subscriber: MockSubscriber) -> None:
        publisher.append(1)
        subscriber.unnotify()
        del publisher[0]
        assert subscriber.notified

    def test_iter_returns_list_elements(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        publisher.append(3)
        iterated = [item for item in publisher]
        assert iterated == [1, 2, 3]

    def test_len_returns_length(self, publisher: ListPublisher[int]) -> None:
        publisher.append(1)
        publisher.append(2)
        assert len(publisher) == 2
