from collections import deque
from typing import Dict, Any, List

class ECUQueue:
    def __init__(self) -> None:
        self.q: deque[Dict[str, Any]] = deque()

    def push_many(self, actions: List[Dict[str, Any]]) -> None:
        for a in actions:
            self.q.append(a)

    def drain_sim(self) -> int:
        """Simulate sending all queued actions to ECU. Returns count."""
        n = 0
        while self.q:
            _ = self.q.popleft()
            n += 1
        return n

queue = ECUQueue()
