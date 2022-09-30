from typing import List
from pymergen.entity.command import EntityCommand
from pymergen.controller.controller import Controller


class ControllerGroup:

    DIR_BASE = "/sys/fs/cgroup"

    def __init__(self, name: str):
        self._name = name
        self._become_cmd = None
        self._controllers = list()

    @property
    def name(self) -> str:
        return self._name

    @property
    def become_cmd(self) -> str:
        return self._become_cmd

    @become_cmd.setter
    def become_cmd(self, value: str) -> None:
        self._become_cmd = value

    @property
    def controllers(self) -> List[Controller]:
        return self._controllers

    @controllers.setter
    def controllers(self, values: List[Controller]) -> None:
        self._controllers = values

    def add_controller(self, value: Controller) -> None:
        self._controllers.append(value)

    def builders(self) -> List[EntityCommand]:
        commands = list()
        c = EntityCommand()
        c.name = "cgcreate_{cgroup}".format(cgroup=self.name)
        c.cmd = "cgcreate -g {controllers}:{cgroup}".format(
            controllers=",".join(self._controller_names()),
            cgroup=self.name
        )
        c.become_cmd = self.become_cmd
        commands.append(c)
        for controller in self.controllers:
            for key, value in controller.limits.items():
                c = EntityCommand()
                c.name = "cgset_{cgroup}_{controller}_{key}".format(cgroup=self.name, controller=controller.name, key=key)
                c.cmd = "cgset -r {controller}.{key}={value} {cgroup}".format(
                    controller=controller.name,
                    key=key, value=value,
                    cgroup=self.name)
                c.become_cmd = self.become_cmd
                commands.append(c)
        return commands

    def destroyers(self) -> List[EntityCommand]:
        commands = list()
        c = EntityCommand()
        c.name = "cgdelete_{cgroup}".format(cgroup=self.name)
        c.cmd = "cgdelete -g {controllers}:{cgroup}".format(
            controllers=",".join(self._controller_names()),
            cgroup=self.name
        )
        c.become_cmd = self.become_cmd
        commands.append(c)
        return commands

    def _controller_names(self) -> List[str]:
        return [c.name for c in self.controllers]
