import pytest
import json
from unittest.mock import MagicMock, patch
from pymergen.core.runner import Runner
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand
from pymergen.core.executor import (
    ControllingExecutor, CollectingExecutor, ReplicatingExecutor,
    ConcurrentExecutor, IteratingExecutor, ParallelExecutor, ProcessExecutor
)


class TestRunner:
    @pytest.fixture
    def context(self):
        context = MagicMock()
        context.run_path = "/test/run"
        return context

    @pytest.fixture
    def plan(self):
        # Create a basic test plan structure
        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.replication = 1
        plan.collectors = []
        plan.cgroups = []

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.replication = 1
        suite.config.concurrency = False
        plan.add_suite(suite)

        case = EntityCase()
        case.name = "testcase"
        case.config.replication = 1
        case.config.parallelism = 1
        suite.add_case(case)

        command = EntityCommand()
        command.cmd = "echo 'test'"
        case.commands.append(command)

        return plan

    def test_init(self, context):
        runner = Runner(context)
        assert runner.context == context

    @patch.object(ControllingExecutor, 'execute')
    def test_run(self, mock_execute, context, plan):
        # Setup
        runner = Runner(context)

        # Execute
        runner.run([plan])

        # Assert that execute was called
        mock_execute.assert_called_once()

    def test_run_executor_hierarchy(self, context, plan):
        # This test verifies the executor hierarchy is correctly constructed
        runner = Runner(context)

        # Patch the execute method to capture the executor hierarchy
        with patch.object(ControllingExecutor, 'execute', autospec=True) as mock_execute:
            runner.run([plan])

            # Get the controlling executor from the mock call
            controlling_executor = mock_execute.mock_calls[0].args[0]

            # Verify the hierarchy
            assert isinstance(controlling_executor, ControllingExecutor)
            assert len(controlling_executor.children) == 1

            plan_re = controlling_executor.children[0]
            assert isinstance(plan_re, ReplicatingExecutor)
            assert len(plan_re.children) == 1

            suite_re = plan_re.children[0]
            assert isinstance(suite_re, ReplicatingExecutor)
            assert len(suite_re.children) == 1

            # Suite is not configured with concurrency, so there's a ConcurrentExecutor
            suite_cce = suite_re.children[0]
            assert isinstance(suite_cce, ConcurrentExecutor)
            assert len(suite_cce.children) == 1

            case_re = suite_cce.children[0]
            assert isinstance(case_re, ReplicatingExecutor)
            assert len(case_re.children) == 1

            case_ie = case_re.children[0]
            assert isinstance(case_ie, IteratingExecutor)
            assert len(case_ie.children) == 1

            # Suite has concurrency=False, so we get a CollectingExecutor for the case
            case_cle = case_ie.children[0]
            assert isinstance(case_cle, CollectingExecutor)
            assert len(case_cle.children) == 1

            case_pe = case_cle.children[0]
            assert isinstance(case_pe, ParallelExecutor)
            assert len(case_pe.children) == 1

            command_pe = case_pe.children[0]
            assert isinstance(command_pe, ProcessExecutor)

    def test_run_with_concurrency(self, context):
        # Create a plan with concurrency=True in the suite
        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.replication = 1
        plan.collectors = []
        plan.cgroups = []

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.replication = 1
        suite.config.concurrency = True  # Set concurrency to True
        plan.add_suite(suite)

        case = EntityCase()
        case.name = "testcase"
        case.config.replication = 1
        case.config.parallelism = 1
        suite.add_case(case)

        command = EntityCommand()
        command.cmd = "echo 'test'"
        case.commands.append(command)

        runner = Runner(context)

        # Patch the execute method to capture the executor hierarchy
        with patch.object(ControllingExecutor, 'execute', autospec=True) as mock_execute:

            runner.run([plan])

            # Navigate down to the suite level
            controlling_executor = mock_execute.mock_calls[0].args[0]
            plan_re = controlling_executor.children[0]
            suite_re = plan_re.children[0]

            # With concurrency=True, we should have a CollectingExecutor at the suite level
            # followed by a ConcurrentExecutor
            suite_cle = suite_re.children[0]
            assert isinstance(suite_cle, CollectingExecutor)

            suite_cce = suite_cle.children[0]
            assert isinstance(suite_cce, ConcurrentExecutor)

            # Now follow down to the case level
            case_re = suite_cce.children[0]
            case_ie = case_re.children[0]

            # With suite concurrency=True, we should NOT have a CollectingExecutor at the case level
            assert isinstance(case_ie.children[0], ParallelExecutor)

    @patch('os.path.isfile')
    @patch('pymergen.core.runner.glob.glob')
    @patch('pymergen.core.runner.json.dumps')
    @patch('builtins.print')
    def test_report_files(self, mock_print, mock_dumps, mock_glob, mock_isfile, context):
        # Setup
        mock_glob.return_value = [
            "/test/run/plan/r001/suite/r001/case/r001/collector.perf_stat.data",
            "/test/run/plan/r001/suite/r001/case/r001/collector.cgroup_cpu.log"
        ]
        mock_dumps.return_value = '{"files": {"collector": {"collector.perf_stat": ["/test/run/plan/r001/suite/r001/case/r001/collector.perf_stat.data"], "collector.cgroup_cpu": ["/test/run/plan/r001/suite/r001/case/r001/collector.cgroup_cpu.log"]}}'
        mock_isfile.return_value = True

        # Execute
        runner = Runner(context)
        runner.report({"files": True})

        # Assert
        mock_glob.assert_called_once_with("/test/run/**/*", recursive=True)
        mock_dumps.assert_called_once()
        mock_print.assert_called_once()

        # Check that the report structure is correct
        report_dict = mock_dumps.call_args[0][0]
        assert "files" in report_dict
        assert "collector" in report_dict["files"]
        assert "collector.perf_stat" in report_dict["files"]["collector"]
        assert "collector.cgroup_cpu" in report_dict["files"]["collector"]
