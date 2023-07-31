"""
Module that holds the Queue class which acts as a First In First
Out (FIFO) queue

Classes:
    Queue: Represents a FIFO queue
"""

from typing import Any, Optional

class Queue:
    """
    Acts as a First In First Out (FIFO) queue
    """
    def __init__(self, max_length: int = 5):
        self.max_length: int = max_length
        self.list = []

    def push(self, item) -> Optional[Any]:
        """
        Pushes a new item into the queue. If the length of the list is
        a its max length, it will remove the oldest item in the queue

        Args:
            item (Any): The newest item to be added to the list

        Returns:
            Any: The oldest item in the list that was removed to make
                room for the newest item. Returns None if no item was
                removed.
        """
        removed_item = None
        if len(self.list) == self.max_length:
            removed_item = self.remove()
        self.list.append(item)
        return removed_item

    def remove(self) -> Optional[Any]:
        """
        Removes the first (oldest) item in the list

        Returns:
            Any: The first item in the list
        """
        if len(self.list) > 0:
            return self.list.pop(0)
        return None

    def contains(self, item) -> bool:
        """
        Compares the item argument to the each item in the list and
        returns True if any of the items in the list equal the argument

        Args:
            item (Any): Item to be compared to the list items

        Returns:
            bool: Whether there is a match in the list
        """
        return item in self.list
    
    def peak(self) -> Optional[Any]:
        """
        Peaks at the next item to be removed from the queue list

        Returns:
            Any: Item next to be removed. Returns None if is empty.
        """
        if len(self.list) > 0:
            return self.list[0]
        return None

    def __len__(self):
        return len(self.list)

    def __repr__(self):
        return f'{len(self.list)}'
