import pytest
from unittest.mock import MagicMock, patch
import subprocess
import signal
import time
from pymergen.core.process import Process
from pymergen.entity.command import EntityCommand


class TestProcess:
    @pytest.fixture
    def context(self):
        context = MagicMock()
        context.logger = MagicMock()
        return context

    @pytest.fixture
    def command(self):
        cmd = EntityCommand()
        cmd.name = "test"
        cmd.cmd = "echo 'test'"
        cmd.shell = True
        cmd.debug_stdout = False
        cmd.debug_stderr = False
        cmd.pipe_stdout = None
        cmd.pipe_stderr = None
        cmd.timeout = None
        return cmd

    def test_init(self, context):
        process = Process(context)
        assert process.context == context
        assert process._command is None
        assert process._process is None
        assert process._stdout is None
        assert process._stderr is None

    def test_command_property(self, context, command):
        process = Process(context)
        process.command = command
        assert process.command == command

    @patch('pymergen.core.process.subprocess.Popen')
    def test_run_shell_true(self, mock_popen, context, command):
        # Setup
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'test output', b'')
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command
        process.run()

        # Assert
        mock_popen.assert_called_once_with(
            "echo 'test'",
            shell=True,
            executable=None,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        mock_process.communicate.assert_called_once_with(timeout=None)

    @patch('pymergen.core.process.subprocess.Popen')
    def test_run_shell_false(self, mock_popen, context):
        # Setup
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'test output', b'')
        mock_popen.return_value = mock_process

        # Setup command with shell=False
        cmd = EntityCommand()
        cmd.cmd = "echo test"
        cmd.shell = False
        cmd.debug_stdout = False
        cmd.debug_stderr = False

        # Execute
        process = Process(context)
        process.command = cmd
        process.run()

        # Assert
        mock_popen.assert_called_once_with(
            ["echo", "test"],
            shell=False,
            executable=None,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch('pymergen.core.process.subprocess.Popen')
    def test_run_with_pipe_to_files(self, mock_popen, context, command, tmp_path):
        # Setup
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'test output', b'')
        mock_popen.return_value = mock_process

        # Setup command with pipes
        stdout_file = str(tmp_path / "stdout.txt")
        stderr_file = str(tmp_path / "stderr.txt")
        command.pipe_stdout = stdout_file
        command.pipe_stderr = stderr_file

        # Execute
        with patch('builtins.open') as mock_open:
            mock_stdout = MagicMock()
            mock_stderr = MagicMock()
            mock_open.side_effect = [mock_stdout, mock_stderr]

            process = Process(context)
            process.command = command
            process.run()

            # Assert file handling
            mock_open.assert_any_call(stdout_file, "w")
            mock_open.assert_any_call(stderr_file, "w")
            mock_stdout.close.assert_called_once()
            mock_stderr.close.assert_called_once()

    @patch('pymergen.core.process.subprocess.Popen')
    def test_run_with_debug_output(self, mock_popen, context, command):
        # Setup
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'test output', b'test error')
        mock_popen.return_value = mock_process

        # Setup command with debug flags
        command.debug_stdout = True
        command.debug_stderr = True

        # Execute
        process = Process(context)
        process.command = command
        process.run()

        # Assert debug output
        context.logger.debug.assert_any_call(b'test output')
        context.logger.debug.assert_any_call(b'test error')

    @patch('pymergen.core.process.subprocess.Popen')
    def test_timeout_handling(self, mock_popen, context, command):
        # Setup
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="echo 'test'", timeout=1)
        mock_popen.return_value = mock_process

        # Setup command with timeout
        command.timeout = 1

        with pytest.raises(subprocess.TimeoutExpired) as excinfo:
            # Execute
            process = Process(context)
            process.command = command
            process.run()

        # Assert error handling
        mock_process.kill.assert_called_once()

    @patch('pymergen.core.process.subprocess.Popen')
    def test_timeout_handling_no_exception(self, mock_popen, context, command):
        # Setup
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="echo 'test'", timeout=1)
        mock_popen.return_value = mock_process

        # Setup command with timeout
        command.timeout = 1
        # Do not raise timeout
        command.raise_error = False

        try:
            # Execute
            process = Process(context)
            process.command = command
            process.run()
        except Exception as e:
            assert False, "Unexpected exception raised {e}".format(e=e)

        mock_process.kill.assert_called_once()

    @patch('pymergen.core.process.subprocess.Popen')
    def test_signal(self, mock_popen, context, command):
        # Setup
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command
        process.start()
        process.signal(signal.SIGTERM)

        # Assert
        mock_process.send_signal.assert_called_once_with(signal.SIGTERM)

    @patch('pymergen.core.process.subprocess.Popen')
    def test_complex_pipeline_shell_false(self, mock_popen, context):
        # Setup a command with pipes
        cmd = EntityCommand()
        cmd.cmd = "cat /etc/passwd | grep root | wc -l"
        cmd.shell = False

        mock_process1 = MagicMock()
        mock_process1.stdout = MagicMock()

        mock_process2 = MagicMock()
        mock_process2.stdout = MagicMock()

        mock_process3 = MagicMock()
        mock_process3.returncode = 0
        mock_process3.communicate.return_value = (b'1', b'')

        # Make Popen return different mocks for each call
        mock_popen.side_effect = [mock_process1, mock_process2, mock_process3]

        # Execute
        process = Process(context)
        process.command = cmd
        process.run()

        # Assert
        assert mock_popen.call_count == 3
        # First process
        mock_popen.assert_any_call(
            ["cat", "/etc/passwd"],
            shell=False,
            executable=None,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Second process
        mock_popen.assert_any_call(
            ["grep", "root"],
            shell=False,
            executable=None,
            stdin=mock_process1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Third process
        mock_popen.assert_any_call(
            ["wc", "-l"],
            shell=False,
            executable=None,
            stdin=mock_process2.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Verify stdout closing
        mock_process1.stdout.close.assert_called_once()
        mock_process2.stdout.close.assert_called_once()

    def test_command_run_time_property(self, context):
        """Test run_time property of EntityCommand"""
        command = EntityCommand()
        assert command.run_time == 0  # Default value is 0

        command.run_time = 30
        assert command.run_time == 30

        command.run_time = 0
        assert command.run_time == 0

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_with_process_completion(self, mock_sleep, mock_popen, context):
        """Test timer functionality when process completes before timer expires"""
        # Setup
        command = EntityCommand()
        command.name = "test"
        command.cmd = "echo 'test'"
        command.run_time = 10

        mock_process = MagicMock()
        # Process exits on second poll
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command
        process.start()

        # Assert
        assert mock_sleep.call_count == 1  # Sleep called once before process exits
        # Verify process was not terminated by timer
        assert not mock_process.signal.called

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_with_timeout(self, mock_sleep, mock_popen, context):
        """Test timer functionality when timer expires before process completes"""
        # Setup
        command = EntityCommand()
        command.name = "test"
        command.cmd = "sleep 30"
        command.run_time = 5

        mock_process = MagicMock()
        # Process never exits during the timer
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command

        with patch.object(Process, 'signal') as mock_signal:
            process.start()

            # Assert
            assert mock_sleep.call_count == 5  # Sleep called for each second of run_time
            # Verify process was terminated by timer
            mock_signal.assert_called_once()

    @patch('pymergen.core.process.subprocess.Popen')
    def test_run_with_run_time(self, mock_popen, context):
        """Test process execution with run_time setting"""
        # Setup
        command = EntityCommand()
        command.cmd = "echo 'test'"
        command.run_time = 5

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'test output', b'')
        mock_popen.return_value = mock_process

        # Mock the _timer method to verify it's called
        with patch.object(Process, '_timer') as mock_timer:
            process = Process(context)
            process.command = command
            process.run()

            # Assert _timer was called
            mock_timer.assert_called_once()
            # Verify other process execution occurred normally
            mock_process.communicate.assert_called_once_with(timeout=None)

    @pytest.fixture
    def command_with_run_time(self):
        cmd = EntityCommand()
        cmd.name = "test"
        cmd.cmd = "sleep 10"
        cmd.run_time = 5
        return cmd

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_initialization(self, mock_sleep, mock_popen, context, command_with_run_time):
        """Test that timer is properly initialized"""
        # Setup
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        process = Process(context)
        process.command = command_with_run_time
        process.start()
        assert mock_process.poll.call_count == 5

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_early_process_exit(self, mock_sleep, mock_popen, context):
        """Test timer behavior when process exits before timer expires"""
        # Setup
        command = EntityCommand()
        command.name = "test"
        command.cmd = "echo 'test'"
        command.run_time = 10

        mock_process = MagicMock()
        # Process exits after 3 polls
        mock_process.poll.side_effect = [None, None, 0]
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command

        with patch.object(Process, 'signal') as mock_signal:
            process.start()
            # Assert
            assert mock_sleep.call_count == 2  # Sleep called until process exits
            # Verify process was not terminated by timer
            assert not mock_signal.called

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_expiration(self, mock_sleep, mock_popen, context, command_with_run_time):
        """Test timer behavior when timer expires while process is still running"""
        # Setup
        mock_process = MagicMock()
        # Process never exits during timer
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Execute
        process = Process(context)
        process.command = command_with_run_time

        with patch.object(Process, 'signal') as mock_signal:
            process.start()
            # Assert
            assert mock_sleep.call_count == 5  # Sleep called for each second
            # Verify process was terminated when timer expired
            mock_signal.assert_called_once_with()

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_with_zero_run_time(self, mock_sleep, mock_popen, context):
        """Test that timer is not started with zero run_time"""
        # Setup
        command = EntityCommand()
        command.cmd = "echo 'test'"
        command.run_time = 0  # No run_time

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Mock the _timer method to verify it's not called
        with patch.object(Process, '_timer') as mock_timer:
            process = Process(context)
            process.command = command
            process.start()

            # Assert _timer was not called
            mock_timer.assert_not_called()

    @patch('pymergen.core.process.subprocess.Popen')
    @patch('pymergen.core.process.time.sleep')
    def test_timer_with_custom_signal(self, mock_sleep, mock_popen, context):
        """Test that timer uses the correct signal to terminate process"""
        # Setup
        command = EntityCommand()
        command.cmd = "sleep 30"
        command.run_time = 3

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Execute with patched signal method
        process = Process(context)
        process.command = command

        # Replace the signal method with our mock
        with patch.object(Process, 'signal') as mock_signal:
            process.start()

            # Assert signal was called after timer expired
            mock_signal.assert_called_once_with()
