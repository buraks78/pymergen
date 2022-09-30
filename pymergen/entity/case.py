from typing import List
from pymergen.entity.entity import Entity
from pymergen.entity.command import EntityCommand


class EntityCase(Entity):

    def __init__(self):
        super().__init__()
        self._commands = list()

    @property
    def commands(self) -> List[EntityCommand]:
        return self._commands

    @commands.setter
    def commands(self, values: List[EntityCommand]) -> None:
        self._commands = list()
        for value in values:
            self.add_command(value)

    def add_command(self, value: EntityCommand) -> None:
        value.parent = self
        self._commands.append(value)

    def dir_name(self) -> str:
        return "case_{case}".format(case=self.name)

    def short_name(self) -> str:
        return "Case[{case}]".format(case=self.name)

    def long_name(self) -> str:
        return "Plan[{plan}] > Suite[{suite}] > Case[{case}]".format(plan=self.parent.parent.name, suite=self.parent.name, case=self.name)
