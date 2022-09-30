from typing import List
from pymergen.entity.entity import Entity
from pymergen.entity.suite import EntitySuite
from pymergen.controller.group import ControllerGroup
from pymergen.collector.collector import Collector


class EntityPlan(Entity):

    def __init__(self):
        super().__init__()
        self._suites = list()
        self._cgroups = list()
        self._collectors = list()

    @property
    def suites(self) -> List[EntitySuite]:
        return self._suites

    @suites.setter
    def suites(self, values: List[EntitySuite]) -> None:
        self._suites = list()
        for value in values:
            self.add_suite(value)

    def add_suite(self, value: EntitySuite) -> None:
        value.parent = self
        self._suites.append(value)

    @property
    def cgroups(self) -> List[ControllerGroup]:
        return self._cgroups

    @cgroups.setter
    def cgroups(self, values: List[ControllerGroup]) -> None:
        self._cgroups = values

    @property
    def collectors(self) -> List[Collector]:
        return self._collectors

    @collectors.setter
    def collectors(self, values: List[Collector]) -> None:
        self._collectors = values

    def add_collector(self, value: Collector) -> None:
        self._collectors.append(value)

    def dir_name(self) -> str:
        return "plan_{plan}".format(plan=self.name)

    def short_name(self) -> str:
        return "Plan[{plan}]".format(plan=self.name)

    def long_name(self) -> str:
        return self.short_name()
