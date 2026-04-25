from dataclasses import dataclass
from queue import PriorityQueue

event_queue = PriorityQueue()


@dataclass
class Event:
    def __init__(
        self,
        name,
        actor_id,
        target: list = None,
        priority: int = 100,
        data: dict = None,
    ):
        self.name = name
        self.actor_id = actor_id
        self.target = target
        self.priority = priority
        self.data = data


@dataclass
class EventResult:
    def __init__(self, name, data: dict = None):
        self.name = name
        self.data = data
        self.new_events = []
