import os
import pytest
import threading
from unittest.mock import MagicMock, patch, call
from pymergen.core.executor import (
    ExecutorContext, ControllingExecutorContext, CollectingExecutorContext,
    ReplicatingExecutorContext, ConcurrentExecutorContext, ParallelExecutorContext,
    IteratingExecutorContext, Executor, ControllingExecutor, CollectingExecutor,
    ReplicatingExecutor, ConcurrentExecutor, IteratingExecutor, ParallelExecutor,
    ProcessExecutor, AsyncProcessExecutor, AsyncThreadExecutor
)
from pymergen.entity.entity import Entity, EntityConfig
from pymergen.entity.command import EntityCommand
from pymergen.entity.case import EntityCase
from pymergen.entity.suite import EntitySuite
from pymergen.entity.plan import EntityPlan


class TestExecutorContext:
    def test_init(self):
        parent_context = MagicMock()
        context = ExecutorContext(parent_context)

        assert context._parent == parent_context
        assert context._entity is None
        assert context._current is None
        assert context._prefix is None
        assert context._exclude_from_path is False

    def test_properties(self):
        parent_context = MagicMock()
        entity = MagicMock()

        context = ExecutorContext(parent_context)
        context.entity = entity
        context.current = 42

        assert context.parent == parent_context
        assert context.entity == entity
        assert context.current == 42
        assert context.exclude_from_path is False

    def test_id(self):
        context = ExecutorContext(None)
        context._prefix = "test"
        context._current = 7

        assert context.id() == "test007"


class TestDerivedContextClasses:
    def test_controlling_executor_context(self):
        parent_context = MagicMock()
        context = ControllingExecutorContext(parent_context)

        assert context._prefix == "cne"
        assert context._exclude_from_path is True

    def test_collecting_executor_context(self):
        parent_context = MagicMock()
        context = CollectingExecutorContext(parent_context)

        assert context._prefix == "cle"
        assert context._exclude_from_path is True
        assert context._cgroups is None

        # Test cgroups property
        cgroups = [MagicMock()]
        context.cgroups = cgroups
        assert context.cgroups == cgroups

    def test_replicating_executor_context(self):
        parent_context = MagicMock()
        context = ReplicatingExecutorContext(parent_context)

        assert context._prefix == "r"
        assert context._exclude_from_path is False

    def test_concurrent_executor_context(self):
        parent_context = MagicMock()
        context = ConcurrentExecutorContext(parent_context)

        assert context._prefix == "cce"
        assert context._exclude_from_path is True

    def test_parallel_executor_context(self):
        parent_context = MagicMock()
        context = ParallelExecutorContext(parent_context)

        assert context._prefix == "p"
        assert context._exclude_from_path is False

    def test_iterating_executor_context(self):
        parent_context = MagicMock()
        context = IteratingExecutorContext(parent_context)

        assert context._prefix == "i"
        assert context._exclude_from_path is False
        assert context._iters == {}

        # Test iters property
        iters = {"var1": "val1"}
        context.iters = iters
        assert context.iters == iters


class TestExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity(self):
        entity = MagicMock()
        entity.pre = []
        entity.post = []
        return entity

    def test_init(self, context, entity):
        executor = Executor(context, entity)

        assert executor.context == context
        assert executor.entity == entity
        assert executor.children == []

    def test_children_property(self, context, entity):
        executor = Executor(context, entity)
        child1 = MagicMock()
        child2 = MagicMock()

        executor.children = [child1, child2]
        assert executor.children == [child1, child2]

    def test_add_child(self, context, entity):
        executor = Executor(context, entity)
        child = MagicMock()

        executor.add_child(child)
        assert executor.children == [child]

    def test_execute_main_not_implemented(self, context, entity):
        executor = Executor(context, entity)

        with pytest.raises(NotImplementedError):
            executor.execute(MagicMock())

    @patch.object(ProcessExecutor, 'execute')
    def test_execute_pre(self, mock_execute, context, entity):
        # Setup
        pre_command1 = MagicMock()
        pre_command2 = MagicMock()
        entity.pre = [pre_command1, pre_command2]

        executor = Executor(context, entity)
        parent_context = MagicMock()

        # Execute
        executor.execute_pre(parent_context)

        # Assert
        assert mock_execute.call_count == 2

    @patch.object(ProcessExecutor, 'execute')
    def test_execute_post(self, mock_execute, context, entity):
        # Setup
        post_command1 = MagicMock()
        post_command2 = MagicMock()
        entity.post = [post_command1, post_command2]

        executor = Executor(context, entity)
        parent_context = MagicMock()

        # Execute
        executor.execute_post(parent_context)

        # Assert
        assert mock_execute.call_count == 2

    @patch('os.makedirs')
    @patch('os.path.join')
    def test_run_path(self, mock_join, mock_makedirs, context, entity):
        # Setup
        context.run_path = "/test/run"
        mock_join.return_value = "/test/run/entity/r001"

        entity.name = "entity"

        executor = Executor(context, entity)

        # Create a context chain
        child_context = MagicMock()
        child_context.entity = entity
        child_context.id.return_value = "r001"
        child_context.exclude_from_path = False
        child_context.parent = None

        # Execute
        path = executor.run_path(child_context)

        # Assert
        assert path == "/test/run/entity/r001"
        mock_makedirs.assert_called_once_with("/test/run/entity/r001", exist_ok=True)


class TestControllingExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity(self):
        entity = MagicMock()
        entity.pre = []
        entity.post = []
        return entity

    @pytest.fixture
    def cgroups(self):
        cgroup1 = MagicMock()
        cgroup1.builders.return_value = [MagicMock()]
        cgroup1.destroyers.return_value = [MagicMock()]

        cgroup2 = MagicMock()
        cgroup2.builders.return_value = [MagicMock()]
        cgroup2.destroyers.return_value = [MagicMock()]

        return [cgroup1, cgroup2]

    def test_init(self, context, entity, cgroups):
        executor = ControllingExecutor(context, entity, cgroups)

        assert executor.context == context
        assert executor.entity == entity
        assert executor.cgroups == cgroups

    @patch.object(ProcessExecutor, 'execute')
    def test_execute_main(self, mock_process_execute, context, entity, cgroups):
        # Setup
        executor = ControllingExecutor(context, entity, cgroups)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert builder commands were executed
        assert mock_process_execute.call_count == 4  # 2 cgroups with 1 builder + 1 destroyer each

        # Assert child was executed
        child.execute.assert_called_once()

        # Verify context passed to child is of correct type
        context_arg = child.execute.call_args[0][0]
        assert isinstance(context_arg, ControllingExecutorContext)
        assert context_arg.entity == entity


class TestCollectingExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity(self):
        entity = MagicMock()
        entity.pre = []
        entity.post = []
        return entity

    @pytest.fixture
    def collectors(self):
        collector1 = MagicMock()
        collector2 = MagicMock()
        return [collector1, collector2]

    @pytest.fixture
    def cgroups(self):
        return [MagicMock(), MagicMock()]

    def test_init(self, context, entity, collectors, cgroups):
        executor = CollectingExecutor(context, entity, collectors, cgroups)

        assert executor.context == context
        assert executor.entity == entity
        assert executor.collectors == collectors
        assert executor.cgroups == cgroups
        assert executor.executors == []

    def test_execute_main(self, context, entity, collectors, cgroups):
        # Setup
        executor = CollectingExecutor(context, entity, collectors, cgroups)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert collectors were started
        for collector in collectors:
            collector.start.assert_called_once()
            collector.stop.assert_called_once()

        # Assert child was executed
        child.execute.assert_called_once()

        # Verify context passed to collector and child
        for collector in collectors:
            context_arg = collector.start.call_args[0][0]
            assert isinstance(context_arg, CollectingExecutorContext)
            assert context_arg.entity == entity
            assert context_arg.cgroups == cgroups


class TestReplicatingExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity(self):
        entity = MagicMock()
        entity.config = MagicMock()
        entity.config.replication = 2
        entity.pre = []
        entity.post = []
        entity.log_name.return_value = "test_entity"
        return entity

    def test_execute_main(self, context, entity):
        # Setup
        executor = ReplicatingExecutor(context, entity)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()
        parent_context.parent = None

        # Mock execute_pre and execute_post to avoid external dependencies
        executor.execute_pre = MagicMock()
        executor.execute_post = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert
        assert executor.execute_pre.call_count == 2  # Called once per replication
        assert executor.execute_post.call_count == 2  # Called once per replication
        assert child.execute.call_count == 2  # Called once per replication

        # Verify contexts passed to child
        for call_args in child.execute.call_args_list:
            context_arg = call_args[0][0]
            assert isinstance(context_arg, ReplicatingExecutorContext)
            assert context_arg.entity == entity
            assert context_arg.current in [1, 2]  # Should be called with r=1 and r=2

    @patch('builtins.open')
    def test_stat_tracking_and_logging(self, mock_open, context, entity):
        # Setup
        executor = ReplicatingExecutor(context, entity)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Mock run_path to return a predictable path
        test_path = "/test/run/path"
        executor.run_path = MagicMock(return_value=test_path)

        mock_stat = MagicMock()
        mock_stat.timer = MagicMock(return_value=MagicMock())
        mock_stat.timer.duration = MagicMock(return_value=10.5)
        mock_stat.timer.log = MagicMock()

        executor.stat = MagicMock()
        executor.stat.return_value = mock_stat

        # Mock pre and post execution to simplify the test
        executor.execute_pre = MagicMock()
        executor.execute_post = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Verify Stat methods were called properly
        assert mock_stat.start.call_count == 2
        assert mock_stat.stop.call_count == 2
        assert mock_stat.log.call_count == 2

        # Verify log method was called with correct path
        for call_args in mock_stat.log.call_args_list:
            assert call_args[0][0] == test_path


class TestConcurrentExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity_concurrent(self):
        entity = MagicMock()
        entity.config = MagicMock()
        entity.config.concurrency = True
        entity.log_name.return_value = "test_entity"
        return entity

    @pytest.fixture
    def entity_not_concurrent(self):
        entity = MagicMock()
        entity.config = MagicMock()
        entity.config.concurrency = False
        entity.log_name.return_value = "test_entity"
        return entity

    @patch('pymergen.core.executor.threading.Thread')
    def test_execute_main_concurrent(self, mock_thread_class, context, entity_concurrent):
        # Setup
        mock_thread1 = MagicMock()
        mock_thread2 = MagicMock()
        mock_thread_class.side_effect = [mock_thread1, mock_thread2]

        executor = ConcurrentExecutor(context, entity_concurrent)
        child1 = MagicMock()
        child2 = MagicMock()
        executor.add_child(child1)
        executor.add_child(child2)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert
        assert mock_thread_class.call_count == 2
        mock_thread1.start.assert_called_once()
        mock_thread2.start.assert_called_once()
        mock_thread1.join.assert_called_once()
        mock_thread2.join.assert_called_once()

        # Check thread targets point to child.execute
        thread1_args = mock_thread_class.call_args_list[0][1]
        thread2_args = mock_thread_class.call_args_list[1][1]
        assert thread1_args['target'] == child1.execute
        assert thread2_args['target'] == child2.execute

        # Verify contexts passed to threads
        context1 = thread1_args['args'][0]
        context2 = thread2_args['args'][0]
        assert isinstance(context1, ConcurrentExecutorContext)
        assert isinstance(context2, ConcurrentExecutorContext)
        assert context1.entity == entity_concurrent
        assert context2.entity == entity_concurrent
        assert context1.current == 1
        assert context2.current == 2

    def test_execute_main_not_concurrent(self, context, entity_not_concurrent):
        # Setup
        executor = ConcurrentExecutor(context, entity_not_concurrent)
        child1 = MagicMock()
        child2 = MagicMock()
        executor.add_child(child1)
        executor.add_child(child2)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert children were executed sequentially
        child1.execute.assert_called_once()
        child2.execute.assert_called_once()

        # Verify contexts passed to children
        context1 = child1.execute.call_args[0][0]
        context2 = child2.execute.call_args[0][0]
        assert isinstance(context1, ConcurrentExecutorContext)
        assert isinstance(context2, ConcurrentExecutorContext)
        assert context1.entity == entity_not_concurrent
        assert context2.entity == entity_not_concurrent
        assert context1.current == 1
        assert context2.current == 1


class TestIteratingExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity_with_iters(self):
        entity = MagicMock()
        entity.parent = None
        entity.config = MagicMock()
        entity.config.iters = {"var1": ["A", "B"], "var2": ["C", "D"]}
        entity.config.iteration = EntityConfig.ITERATION_TYPE_PRODUCT
        entity.log_name.return_value = "test_entity"
        return entity

    @pytest.fixture
    def entity_without_iters(self):
        entity = MagicMock()
        entity.parent = None
        entity.config = MagicMock()
        entity.config.iters = {}
        entity.log_name.return_value = "test_entity"
        return entity

    def test_execute_main_with_iters_product(self, context, entity_with_iters):
        # Setup
        executor = IteratingExecutor(context, entity_with_iters)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert - with product iteration we should get 4 executions (2x2)
        assert child.execute.call_count == 4

        # Collect all iteration contexts passed to the child
        iter_contexts = [call_args[0][0] for call_args in child.execute.call_args_list]

        # Verify all 4 combinations were passed
        expected_combinations = [
            {"var1": "A", "var2": "C"},
            {"var1": "A", "var2": "D"},
            {"var1": "B", "var2": "C"},
            {"var1": "B", "var2": "D"}
        ]

        for context in iter_contexts:
            assert isinstance(context, IteratingExecutorContext)
            assert context.entity == entity_with_iters
            assert context.iters in expected_combinations
            expected_combinations.remove(context.iters)  # Remove to ensure no duplicates

        assert len(expected_combinations) == 0  # All combinations should be used

    def test_execute_main_with_iters_zip(self, context):
        # Setup entity with zip iteration
        entity = MagicMock()
        entity.parent = None
        entity.config = MagicMock()
        entity.config.iters = {"var1": ["A", "B"], "var2": ["C", "D"]}
        entity.config.iteration = EntityConfig.ITERATION_TYPE_ZIP
        entity.log_name.return_value = "test_entity"

        executor = IteratingExecutor(context, entity)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert - with zip iteration we should get 2 executions
        assert child.execute.call_count == 2

        # Collect all iteration contexts passed to the child
        iter_contexts = [call_args[0][0] for call_args in child.execute.call_args_list]

        # Verify the 2 combinations were passed
        expected_combinations = [
            {"var1": "A", "var2": "C"},
            {"var1": "B", "var2": "D"}
        ]

        for context in iter_contexts:
            assert isinstance(context, IteratingExecutorContext)
            assert context.entity == entity
            assert context.iters in expected_combinations
            expected_combinations.remove(context.iters)  # Remove to ensure no duplicates

        assert len(expected_combinations) == 0  # All combinations should be used

    def test_execute_main_without_iters(self, context, entity_without_iters):
        # Setup
        executor = IteratingExecutor(context, entity_without_iters)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert - no iteration, so child should be executed once
        child.execute.assert_called_once()

        # Verify context passed to child
        context_arg = child.execute.call_args[0][0]
        assert isinstance(context_arg, IteratingExecutorContext)
        assert context_arg.entity == entity_without_iters
        assert context_arg.current == 1
        assert context_arg.iters == {}  # Empty iteration dictionary


class TestParallelExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity_parallel(self):
        entity = MagicMock()
        entity.config = MagicMock()
        entity.config.parallelism = 3
        entity.log_name.return_value = "test_entity"
        return entity

    @pytest.fixture
    def entity_not_parallel(self):
        entity = MagicMock()
        entity.config = MagicMock()
        entity.config.parallelism = 1
        entity.log_name.return_value = "test_entity"
        return entity

    @patch('pymergen.core.executor.threading.Thread')
    @patch('pymergen.core.executor.copy.copy')
    def test_execute_main_parallel(self, mock_copy, mock_thread_class, context, entity_parallel):
        # Setup
        mock_thread1 = MagicMock()
        mock_thread2 = MagicMock()
        mock_thread3 = MagicMock()
        mock_thread_class.side_effect = [mock_thread1, mock_thread2, mock_thread3]

        child = MagicMock()
        child_copy1 = MagicMock()
        child_copy2 = MagicMock()
        child_copy3 = MagicMock()
        mock_copy.side_effect = [child_copy1, child_copy2, child_copy3]

        executor = ParallelExecutor(context, entity_parallel)
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert
        assert mock_copy.call_count == 3  # Child should be copied for each parallel instance
        assert mock_thread_class.call_count == 3  # 3 threads for parallelism=3

        # Verify threads were started and joined
        mock_thread1.start.assert_called_once()
        mock_thread2.start.assert_called_once()
        mock_thread3.start.assert_called_once()
        mock_thread1.join.assert_called_once()
        mock_thread2.join.assert_called_once()
        mock_thread3.join.assert_called_once()

        # Check thread targets point to child_copy.execute
        thread1_args = mock_thread_class.call_args_list[0][1]
        thread2_args = mock_thread_class.call_args_list[1][1]
        thread3_args = mock_thread_class.call_args_list[2][1]
        assert thread1_args['target'] == child_copy1.execute
        assert thread2_args['target'] == child_copy2.execute
        assert thread3_args['target'] == child_copy3.execute

        # Verify contexts passed to threads
        context1 = thread1_args['args'][0]
        context2 = thread2_args['args'][0]
        context3 = thread3_args['args'][0]
        assert isinstance(context1, ParallelExecutorContext)
        assert isinstance(context2, ParallelExecutorContext)
        assert isinstance(context3, ParallelExecutorContext)
        assert context1.entity == entity_parallel
        assert context2.entity == entity_parallel
        assert context3.entity == entity_parallel
        assert context1.current == 1
        assert context2.current == 2
        assert context3.current == 3

    def test_execute_main_not_parallel(self, context, entity_not_parallel):
        # Setup
        executor = ParallelExecutor(context, entity_not_parallel)
        child = MagicMock()
        executor.add_child(child)
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)

        # Assert - no parallelism, so child should be executed once directly
        child.execute.assert_called_once()

        # Verify context passed to child
        context_arg = child.execute.call_args[0][0]
        assert isinstance(context_arg, ParallelExecutorContext)
        assert context_arg.entity == entity_not_parallel
        assert context_arg.current == 1


class TestProcessExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def parent_context(self):
        context = MagicMock()
        context.parent = None
        return context

    @pytest.fixture
    def command(self):
        command = EntityCommand()
        command.name = "testcommand"
        command.cmd = "echo 'test'"
        command.shell = False
        command.pipe_stdout = None
        command.pipe_stderr = None
        command.become_cmd = None
        command.cgroups = []
        return command

    @patch('pymergen.core.executor.Process')
    def test_init_and_execute(self, mock_process_class, context, parent_context, command):
        # Setup
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # Create entity hierarchy for placeholder substitution
        case = EntityCase()
        case.name = "testcase"
        case.config.params = {"case_param": "case_value"}

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.params = {"suite_param": "suite_value"}
        suite.add_case(case)

        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.params = {"plan_param": "plan_value"}
        plan.add_suite(suite)

        # Link command to case
        command.parent = case

        # Setup for run_path method
        executor = ProcessExecutor(context, command)
        executor.run_path = MagicMock(return_value="/test/run/path")

        # Execute
        executor.execute_main(parent_context)

        # Assert
        mock_process_class.assert_called_once_with(context)
        mock_process.run.assert_called_once()

        # Verify command was prepared and set on process
        prepared_command = mock_process.command
        assert prepared_command is not command  # Should be a copy
        assert prepared_command.cmd == "echo 'test'"  # Original command without placeholders

    @patch('pymergen.core.executor.copy.copy')
    def test_command_preparation(self, mock_copy, context, parent_context):

        # Setup - create a command with placeholders
        command = EntityCommand()
        command.name = "testcommand"
        command.cmd = "echo '{m:entity:plan} {m:entity:suite} {m:entity:case} {m:entity:command} {m:param:plan_param} {m:param:suite_param} {m:param:case_param} {m:iter:plan_iter} {m:iter:suite_iter} {m:iter:case_iter} {m:context:run_path}'"
        command.pipe_stdout = "{m:context:run_path}/stdout.txt"
        command.pipe_stderr = "{m:context:run_path}/stderr.txt"
        command.shell = False

        # Create entity hierarchy
        case = EntityCase()
        case.name = "testcase"
        case.config.params = {"case_param": "case_value"}
        case.config.iters = {"case_iter": ["case_val1", "case_val2"]}

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.params = {"suite_param": "suite_value"}
        suite.config.iters = {"suite_iter": ["suite_val1", "suite_val2"]}
        suite.add_case(case)

        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.params = {"plan_param": "plan_value"}
        plan.config.iters = {"plan_iter": ["plan_val1", "plan_val2"]}
        plan.add_suite(suite)

        # Link command to case
        command.parent = case

        # Mock the copy call to return a new command object
        command_copy = EntityCommand()
        command_copy.cmd = command.cmd
        command_copy.pipe_stdout = command.pipe_stdout
        command_copy.pipe_stderr = command.pipe_stderr
        command_copy.shell = command.shell
        command_copy.parent = command.parent
        mock_copy.return_value = command_copy

        # Setup executor
        executor = ProcessExecutor(context, command)
        executor.run_path = MagicMock(return_value="/test/run/path")
        executor._sub_cgroup = MagicMock(side_effect=lambda x: x)
        executor._sub_become = MagicMock(side_effect=lambda x: x)

        # Create parent contexts with iteration variables
        parent_plan_context = IteratingExecutorContext(None)
        parent_plan_context.entity = plan
        parent_plan_context.iters = {"plan_iter": "plan_val1"}

        parent_suite_context = IteratingExecutorContext(parent_plan_context)
        parent_suite_context.entity = suite
        parent_suite_context.iters = {"suite_iter": "suite_val1"}

        parent_case_context = IteratingExecutorContext(parent_suite_context)
        parent_case_context.entity = case
        parent_case_context.iters = {"case_iter": "case_val1"}

        # Execute
        prepared_command = executor._command(parent_case_context)

        # Assert placeholders were substituted
        assert prepared_command.cmd == "echo 'testplan testsuite testcase testcommand plan_value suite_value case_value plan_val1 suite_val1 case_val1 /test/run/path'"
        assert prepared_command.pipe_stdout == "/test/run/path/stdout.txt"
        assert prepared_command.pipe_stderr == "/test/run/path/stderr.txt"

    def test_sub_entity(self, context):
        # Test with command under case
        command1 = EntityCommand()
        command1.name = "testcommand"
        case = EntityCase()
        case.name = "testcase"
        suite = EntitySuite()
        suite.name = "testsuite"
        plan = EntityPlan()
        plan.name = "testplan"

        suite.add_case(case)
        plan.add_suite(suite)
        command1.parent = case

        executor1 = ProcessExecutor(context, command1)
        result1 = executor1._sub_entity("Command {m:entity:command} from {m:entity:case} in {m:entity:suite} of {m:entity:plan}")
        assert result1 == "Command testcommand from testcase in testsuite of testplan"

        # Test with command under suite
        command2 = EntityCommand()
        command2.name = "testcommandforsuite"
        command2.parent = suite

        executor2 = ProcessExecutor(context, command2)
        result2 = executor2._sub_entity("Command {m:entity:command} from {m:entity:suite} of {m:entity:plan}")
        assert result2 == "Command testcommandforsuite from testsuite of testplan"

        # Test with command under plan
        command3 = EntityCommand()
        command3.name = "testcommandforplan"
        command3.parent = plan

        executor3 = ProcessExecutor(context, command3)
        result3 = executor3._sub_entity("Command {m:entity:command} from {m:entity:plan}")
        assert result3 == "Command testcommandforplan from testplan"

    def test_sub_params(self, context):
        # Setup entity hierarchy with params
        command = EntityCommand()

        case = EntityCase()
        case.config.params = {"case_param": "case_value", "shared_param": "case_shared"}

        suite = EntitySuite()
        suite.config.params = {"suite_param": "suite_value", "shared_param": "suite_shared"}

        plan = EntityPlan()
        plan.config.params = {"plan_param": "plan_value", "shared_param": "plan_shared"}

        suite.add_case(case)
        plan.add_suite(suite)
        command.parent = case

        executor = ProcessExecutor(context, command)

        # Test parameter substitution with params from different levels
        result = executor._sub_params("Params: {m:param:case_param} {m:param:suite_param} {m:param:plan_param} {m:param:shared_param}")

        # Verify parameters were substituted
        assert result == "Params: case_value suite_value plan_value case_shared"
        # Note: shared_param should use the closest value (case level)

    def test_sub_iters(self, context):
        # Setup entity hierarchy with iteration variables at different levels
        command = EntityCommand()
        command.name = "testcommand"
        command.cmd = "echo Test"

        case = EntityCase()
        case.name = "testcase"
        case.config.iters = {"case_iter": ["case_val1", "case_val2"]}

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.iters = {"suite_iter": ["suite_val1", "suite_val2"]}

        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.iters = {"plan_iter": ["plan_val1", "plan_val2"]}

        # Setup hierarchy
        suite.add_case(case)
        plan.add_suite(suite)
        command.parent = case

        executor = ProcessExecutor(context, command)

        # Test with iteration variables defined at different levels
        parent_context = IteratingExecutorContext(None)
        parent_context.iters = {"case_iter": "case_val1", "suite_iter": "suite_val1", "plan_iter": "plan_val1"}
        result = executor._sub_iters("Test {m:iter:case_iter} and {m:iter:suite_iter} and {m:iter:plan_iter}", parent_context)

        # Verify iteration variables from all levels were correctly substituted
        assert result == "Test case_val1 and suite_val1 and plan_val1"

        # Test with parent context hierarchy to ensure traversal works correctly
        parent_suite_context = IteratingExecutorContext(None)
        parent_suite_context.entity = suite
        parent_suite_context.current = 1
        parent_suite_context.iters = {"suite_iter": "suite_val1", "plan_iter": "plan_val1"}

        parent_case_context = IteratingExecutorContext(parent_suite_context)
        parent_case_context.entity = case
        parent_case_context.current = 1
        parent_case_context.iters = {"case_iter": "case_val1"}

        # Test iteration variables in nested parent contexts
        test_cmd = "Test {m:iter:case_iter} and {m:iter:suite_iter} and {m:iter:plan_iter}"
        processed_cmd = executor._prepare_placeholders(test_cmd, parent_case_context)

        # Verify iteration variables from all parent contexts were correctly substituted
        assert processed_cmd == "Test case_val1 and suite_val1 and plan_val1"

    def test_sub_become(self, context):
        # Setup
        command = EntityCommand()
        command.become_cmd = "sudo -u testuser"

        executor = ProcessExecutor(context, command)

        # Case 1: become_cmd specified
        result1 = executor._sub_become("echo 'test'")
        assert result1 == "sudo -u testuser echo 'test'"

        # Case 2: No become_cmd specified
        command.become_cmd = None
        result2 = executor._sub_become("echo 'test'")
        assert result2 == "echo 'test'"  # No sudo needed

    @patch('pymergen.core.executor.os.getpid')
    @patch('pymergen.core.executor.os.getppid')
    @patch('pymergen.core.executor.os.getpgid')
    def test_sub_context(self, mock_getpgid, mock_getppid, mock_getpid, context, parent_context):
        # Setup
        mock_getpid.return_value = 1000
        mock_getppid.return_value = 999
        mock_getpgid.return_value = 1001

        command = EntityCommand()
        command.cmd = "test command"

        executor = ProcessExecutor(context, command)
        executor.run_path = MagicMock(return_value="/test/run/path")

        # Test all context placeholder substitutions
        test_cmd = "Path: {m:context:run_path}, PID: {m:context:pid}, PPID: {m:context:ppid}, PGID: {m:context:pgid}"
        result = executor._sub_context(test_cmd, parent_context)

        # Verify all placeholders were correctly substituted
        assert result == "Path: /test/run/path, PID: 1000, PPID: 999, PGID: 1001"


class TestAsyncProcessExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def command(self):
        command = EntityCommand()
        command.cmd = "echo 'test'"
        return command

    @patch('pymergen.core.executor.Process')
    def test_async_execution(self, mock_process_class, context, command):
        # Setup
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        executor = AsyncProcessExecutor(context, command)
        parent_context = MagicMock()

        # Mock command preparation to avoid dependencies
        executor._command = MagicMock(return_value=command)

        # Execute
        executor.execute_main(parent_context)
        executor.execute_stop()

        # Assert
        mock_process_class.assert_called_once_with(context)
        mock_process.start.assert_called_once()
        mock_process.signal.assert_called_once()
        mock_process.wait.assert_called_once()


class TestAsyncThreadExecutor:
    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def entity(self):
        return MagicMock()

    @patch('pymergen.core.executor.Thread')
    def test_async_thread_execution(self, mock_thread_class, context, entity):
        # Setup
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        target = MagicMock()

        executor = AsyncThreadExecutor(context, entity)
        executor.target = target
        parent_context = MagicMock()

        # Execute
        executor.execute_main(parent_context)
        executor.execute_stop()

        # Assert
        mock_thread_class.assert_called_once_with(context)
        mock_thread.run.assert_called_once_with(target, [parent_context])
        target.join.assert_called_once()
        mock_thread.join.assert_called_once()
