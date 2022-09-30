import pytest
from pymergen.entity.command import EntityCommand
from pymergen.entity.case import EntityCase
from pymergen.entity.suite import EntitySuite
from pymergen.entity.plan import EntityPlan


@pytest.fixture
def command():
    return EntityCommand()


class TestCommand:
    def test_command_init(self, command):
        """Test command initialization"""
        assert command._cmd is None
        assert command._become_cmd is None
        assert command._shell is False
        assert command._shell_executable is None
        assert command._timeout is None
        assert command._pipe_stdout is None
        assert command._pipe_stderr is None
        assert command._debug_stdout is False
        assert command._debug_stderr is False
        assert command._cgroups == []


    def test_command_cmd(self, command):
        """Test cmd property"""
        assert command.cmd is None

        command.cmd = "echo test"
        assert command.cmd == "echo test"


    def test_command_become_cmd(self, command):
        """Test become_cmd property"""
        assert command.become_cmd is None

        command.become_cmd = "sudo -i"
        assert command.become_cmd == "sudo -i"


    def test_command_shell(self, command):
        """Test shell property"""
        assert command.shell is False

        command.shell = True
        assert command.shell is True


    def test_command_shell_executable(self, command):
        """Test shell_executable property"""
        assert command.shell_executable is None

        command.shell_executable = "/bin/bash"
        assert command.shell_executable == "/bin/bash"


    def test_command_timeout(self, command):
        """Test timeout property"""
        assert command.timeout is None

        command.timeout = 30
        assert command.timeout == 30


    def test_command_pipe_stdout(self, command):
        """Test pipe_stdout property"""
        assert command.pipe_stdout is None

        command.pipe_stdout = "/path/to/stdout.log"
        assert command.pipe_stdout == "/path/to/stdout.log"


    def test_command_pipe_stderr(self, command):
        """Test pipe_stderr property"""
        assert command.pipe_stderr is None

        command.pipe_stderr = "/path/to/stderr.log"
        assert command.pipe_stderr == "/path/to/stderr.log"


    def test_command_debug_stdout(self, command):
        """Test debug_stdout property"""
        assert command.debug_stdout is False

        command.debug_stdout = True
        assert command.debug_stdout is True


    def test_command_debug_stderr(self, command):
        """Test debug_stderr property"""
        assert command.debug_stderr is False

        command.debug_stderr = True
        assert command.debug_stderr is True


    def test_command_cgroups(self, command):
        """Test cgroups property"""
        assert command.cgroups == []

        command.cgroups = ["cpu", "memory"]
        assert command.cgroups == ["cpu", "memory"]


    def test_command_dir_name(self, command):
        """Test dir_name method"""
        command.name = "testcmd"
        assert command.dir_name() == "command_testcmd"


    def test_command_log_name(self):
        """Test log_name method"""
        # Create a complete hierarchy
        plan = EntityPlan()
        plan.name = "testplan"

        suite = EntitySuite()
        suite.name = "testsuite"

        case = EntityCase()
        case.name = "testcase"

        command = EntityCommand()
        command.name = "testcmd"

        # Link them
        plan.add_suite(suite)
        suite.add_case(case)
        case.add_command(command)

        expected_short = "Command[testcmd]"
        expected_long = "Plan[testplan] > Suite[testsuite] > Case[testcase] > Command[testcmd]"

        assert command.short_name() == expected_short
        assert command.long_name() == expected_long
