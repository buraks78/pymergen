import threading
from typing import List
from pymergen.core.context import Context


class Thread:

    def __init__(self, context: Context):
        self._context = context
        self._type = None
        self._thread = None

    @property
    def context(self) -> Context:
        return self._context

    def run(self, target, args: List) -> None:
        self._type = type(target).__name__
        self.context.logger.debug("Thread[{type}] Run[name={name}]".format(type=self._type, name=target.name))
        self._thread = threading.Thread(name=target.name, target=target.run, args=args)
        self._thread.start()

    def join(self) -> None:
        self.context.logger.debug("Thread[{type}] Join[name={name}]".format(type=self._type, name=self._thread.name))
        self._thread.join()
