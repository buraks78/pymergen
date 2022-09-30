from typing import List
from pymergen.entity.entity import Entity
from pymergen.entity.case import EntityCase


class EntitySuite(Entity):

    def __init__(self):
        super().__init__()
        self._cases = list()

    @property
    def cases(self) -> List[EntityCase]:
        return self._cases

    @cases.setter
    def cases(self, values: List[EntityCase]) -> None:
        self._cases = list()
        for value in values:
            self.add_case(value)

    def add_case(self, value: EntityCase) -> None:
        value.parent = self
        self._cases.append(value)

    def dir_name(self) -> str:
        return "suite_{suite}".format(suite=self.name)

    def short_name(self) -> str:
        return "Suite[{suite}]".format(suite=self.name)

    def long_name(self) -> str:
        return "Plan[{plan}] > Suite[{suite}]".format(plan=self.parent.name, suite=self.name)
