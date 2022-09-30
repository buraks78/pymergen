from typing import List
from pymergen.entity.entity import Entity


class EntityCommand(Entity):

    def __init__(self):
        super().__init__()
        self._cmd = None
        self._become_cmd = None
        self._raise_error = True
        self._run_time = 0
        self._shell = False
        self._shell_executable = None
        self._timeout = None
        self._pipe_stdout = None
        self._pipe_stderr = None
        self._debug_stdout = False
        self._debug_stderr = False
        self._cgroups = list()

    @property
    def cmd(self) -> str:
        return self._cmd

    @cmd.setter
    def cmd(self, value: str) -> None:
        self._cmd = value

    @property
    def become_cmd(self) -> str:
        return self._become_cmd

    @become_cmd.setter
    def become_cmd(self, value: str) -> None:
        self._become_cmd = value

    @property
    def raise_error(self) -> bool:
        return self._raise_error

    @raise_error.setter
    def raise_error(self, value: bool) -> None:
        self._raise_error = value

    @property
    def run_time(self) -> int:
        return self._run_time

    @run_time.setter
    def run_time(self, value: int) -> None:
        self._run_time = value

    @property
    def shell(self) -> bool:
        return self._shell

    @shell.setter
    def shell(self, value: bool) -> None:
        self._shell = value

    @property
    def shell_executable(self) -> str:
        return self._shell_executable

    @shell_executable.setter
    def shell_executable(self, value: str) -> None:
        self._shell_executable = value

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: int) -> None:
        self._timeout = value

    @property
    def pipe_stdout(self) -> str:
        return self._pipe_stdout

    @pipe_stdout.setter
    def pipe_stdout(self, value: str) -> None:
        self._pipe_stdout = value

    @property
    def pipe_stderr(self) -> str:
        return self._pipe_stderr

    @pipe_stderr.setter
    def pipe_stderr(self, value: str) -> None:
        self._pipe_stderr = value

    @property
    def debug_stdout(self) -> bool:
        return self._debug_stdout

    @debug_stdout.setter
    def debug_stdout(self, value: bool) -> None:
        self._debug_stdout = value

    @property
    def debug_stderr(self) -> bool:
        return self._debug_stderr

    @debug_stderr.setter
    def debug_stderr(self, value: bool) -> None:
        self._debug_stderr = value

    @property
    def cgroups(self) -> List[str]:
        return self._cgroups

    @cgroups.setter
    def cgroups(self, values: List[str]) -> None:
        self._cgroups = values

    def dir_name(self) -> str:
        return "command_{command}".format(command=self.name)

    def short_name(self) -> str:
        return "Command[{command}]".format(command=self.name)

    def long_name(self) -> str:
        return "Plan[{plan}] > Suite[{suite}] > Case[{case}] > Command[{command}]".format(plan=self.parent.parent.parent.name, suite=self.parent.parent.name, case=self.parent.name, command=self.name)
