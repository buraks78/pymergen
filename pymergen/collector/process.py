from typing import Dict
from pymergen.collector.collector import Collector
from pymergen.entity.command import EntityCommand
from pymergen.core.executor import ExecutorContext, AsyncProcessExecutor


class CollectorProcess(Collector):

    def __init__(self):
        super().__init__()
        self._executor = None
        self._cmd = None
        self._become_cmd = None
        self._shell = False
        self._shell_executable = None
        self._pipe_stdout = None
        self._pipe_stderr = None

    def parse(self, config: Dict) -> None:
        super().parse(config)
        self._cmd = config.get("cmd", None)
        self._become_cmd = config.get("become_cmd", None)
        self._shell = config.get("shell", False)
        self._shell_executable = config.get("shell_executable", None)
        self._pipe_stdout = config.get("pipe_stdout", None)
        self._pipe_stderr = config.get("pipe_stderr", None)

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

    def command(self) -> EntityCommand:
        command = EntityCommand()
        command.name = self.name
        command.cmd = self.cmd
        command.become_cmd = self.become_cmd
        command.shell = self.shell
        command.shell_executable = self.shell_executable
        command.pipe_stdout = self.pipe_stdout
        command.pipe_stderr = self.pipe_stderr
        return command

    def start(self, parent_context: ExecutorContext) -> None:
        self._executor = AsyncProcessExecutor(self.context, self.command())
        self._executor.execute(parent_context)

    def stop(self) -> None:
        self._executor.execute_stop()
