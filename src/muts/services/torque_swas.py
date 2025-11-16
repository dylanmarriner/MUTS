from typing import List, Dict, Any
from .queue import queue

class TorqueSWASService:
    def queue_actions(self, actions: List[Dict[str, Any]]) -> None:
        if actions:
            queue.push_many(actions)
            queue.drain_sim()
