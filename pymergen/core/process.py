import itertools
import subprocess
import shlex
import signal
import threading
import time
from pymergen.core.context import Context
from pymergen.entity.command import EntityCommand


class Process:

    def __init__(self, context: Context):
        self._context = context
        self._command = None
        self._process = None
        self._stdout = None
        self._stderr = None

    @property
    def context(self) -> Context:
        return self._context

    @property
    def command(self) -> EntityCommand:
        return self._command

    @command.setter
    def command(self, command: EntityCommand):
        self._command = command

    def run(self) -> None:
        self.start()
        self.wait()

    def start(self) -> None:
        try:
            self.context.logger.debug("{n} Execute[{cmd}]".format(n=self._command, cmd=self._command.cmd))
            if self._command.pipe_stdout:
                self._stdout = open(self._command.pipe_stdout, "w")
            if self._command.pipe_stderr:
                self._stderr = open(self._command.pipe_stderr, "w")
            self._process = self._popen()
            if self._command.run_time > 0:
                self._timer()
        except Exception as e:
            self.context.logger.error("Failed to start {n} due to {e}".format(n=self._command, e=e))
            if self._command.raise_error:
                raise e

    def signal(self, sig: signal.Signals = signal.SIGINT) -> None:
        if self._process is None:
            self.context.logger.error("No process to signal for {n}".format(n=self._command))
            return
        try:
            self.context.logger.debug("{n} Signal[signal={sig}]".format(n=self._command, sig=sig))
            self._process.send_signal(sig)
        except Exception as e:
            self.context.logger.error("Failed to send signal {sig} to {n} due to {e}".format(sig=sig, n=self._command, e=e))
            if self._process:
                self._process.kill()
            if self._command.raise_error:
                raise e

    def wait(self) -> None:
        if self._process is None:
            self.context.logger.error("No process to wait for {n}".format(n=self._command))
            return
        try:
            stdout, stderr = self._process.communicate(timeout=self._command.timeout)
            if self._command.debug_stdout:
                if self._command.pipe_stdout:
                    self.context.logger.warning("No debugging output will be captured when stdout is piped")
                self.context.logger.debug(stdout)
            if self._command.debug_stderr:
                if self._command.pipe_stderr:
                    self.context.logger.warning("No debugging output will be captured when stderr is piped")
                self.context.logger.debug(stderr)
            self.context.logger.debug("{n} Return[return_code={r}]".format(n=self._command, r=self._process.returncode))
        except subprocess.TimeoutExpired as e:
            self.context.logger.error("Timeout expiration for {n}".format(n=self._command))
            if self._process:
                self._process.kill()
            if self._command.raise_error:
                raise e
        except Exception as e:
            self.context.logger.error("Failed to wait for {n} due to {e}".format(n=self._command, e=e))
            if self._process:
                self._process.kill()
            if self._command.raise_error:
                raise e
        finally:
            if self._stdout:
                self._stdout.close()
            if self._stderr:
                self._stderr.close()

    def _popen(self) -> subprocess.Popen:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        if self._command.shell is True:
            if self._stdout:
                stdout = self._stdout
            if self._stderr:
                stderr = self._stderr
            return subprocess.Popen(self._command.cmd,
                                    shell=True,
                                    executable=self._command.shell_executable,
                                    stdin=None,
                                    stdout=stdout,
                                    stderr=stderr
                                    )
        # shell is False
        # create a list of sub commands by splitting the full command by the pipe character
        cmd_parts = shlex.split(self._command.cmd)
        sub_cmds = list()
        for k, g in itertools.groupby(cmd_parts, lambda x: x == "|"):
            if not k:
                sub_cmds.append(list(g))
        # chain sub commands
        s_curr = None
        s_prev = None
        total_cmds = len(sub_cmds)
        for i, sub_cmd in enumerate(sub_cmds):
            s_curr_stdin = None
            if s_prev is not None:
                s_curr_stdin = s_prev.stdout
            is_last_command = (i == total_cmds - 1)
            if is_last_command and self._stdout:
                stdout = self._stdout
            if is_last_command and self._stderr:
                stderr = self._stderr
            s_curr = subprocess.Popen(sub_cmd,
                                      shell=False,
                                      executable=self._command.shell_executable,
                                      stdin=s_curr_stdin,
                                      stdout=stdout,
                                      stderr=stderr
                                      )
            if s_prev is not None:
                s_prev.stdout.close()
            s_prev = s_curr
        return s_curr

    def _timer(self) -> None:
        self.context.logger.debug(
            "{n} Timer[run_time={run_time}]".format(n=self._command, run_time=self._command.run_time))
        sleep_time = 0
        while sleep_time < self._command.run_time:
            if self._process.poll() is not None:
                self.context.logger.debug("{n} exited with return code {r} before run timer expired".format(n=self._command, r=self._process.returncode))
                return
            time.sleep(1)
            sleep_time += 1
        self.signal()
