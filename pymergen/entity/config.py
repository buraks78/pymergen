from typing import Dict


class EntityConfig:

    ITERATION_TYPE_PRODUCT = "product"
    ITERATION_TYPE_ZIP = "zip"

    def __init__(self):
        self._replication: int = 1
        self._concurrency: bool = False
        self._parallelism: int = 1
        self._iteration: str = self.ITERATION_TYPE_PRODUCT
        self._params: dict = dict()
        self._iters: dict = dict()

    @property
    def replication(self) -> int:
        return self._replication

    @replication.setter
    def replication(self, value: int) -> None:
        self._replication = value

    @property
    def concurrency(self) -> bool:
        return self._concurrency

    @concurrency.setter
    def concurrency(self, value: bool) -> None:
        self._concurrency = value

    @property
    def parallelism(self) -> int:
        return self._parallelism

    @parallelism.setter
    def parallelism(self, value: int) -> None:
        self._parallelism = value

    @property
    def iteration(self) -> str:
        return self._iteration

    @iteration.setter
    def iteration(self, value: str) -> None:
        self._iteration = value

    @property
    def params(self) -> Dict:
        return self._params

    @params.setter
    def params(self, values: Dict) -> None:
        self._params = values

    @property
    def iters(self) -> Dict:
        return self._iters

    @iters.setter
    def iters(self, values: Dict) -> None:
        self._iters = values
