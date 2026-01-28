from __future__ import annotations

from context import Context
from dispatch import Dispatch

class App:
    def __init__(self, context: Context, connected: list[str]):
        self._context = context
        self._connected = connected

    @classmethod
    def init(cls) -> App:
        context = Context.create()()
        connected = context.get_connected()
        return cls(context, connected)
        
    def search_connected(self, read_config: bool = True) -> None:
        self._context.search_cams(read_config)
        self._connected = self._context.get_connected()

    def run(self) -> None:
        self.search_connected(read_config=True)
        
    def quit(self) -> None:
        self._context.release()