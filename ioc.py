from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import threading

@dataclass
class Dispatch:
    device_name: str
    measure: threading.Event
    calculate: threading.Event

class Terminate:
    device_name: str

class MessageKind:
    DISPATCH = 0
    TERMINATE = 1    

@dataclass
class Message:
    kind: MessageKind
    payload: Any

class IOController:
    def __init__(self):
        pass