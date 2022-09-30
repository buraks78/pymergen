from typing import Dict
from pymergen.core.context import Context


class Collector:

    def __init__(self):
        self._name = None
        self._context = None

    def parse(self, config: Dict) -> None:
        self._name = config.get("name")

    @property
    def name(self) -> int:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, value: Context) -> None:
        self._context = value

    def configure(self, config: Dict) -> None:
        pass

    def start(self, value: Context) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()
