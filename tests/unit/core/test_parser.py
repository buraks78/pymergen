import os
import re
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pymergen.core.parser import Parser
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand


class TestParser:
    @pytest.fixture
    def context(self):
        context = MagicMock()
        context.plan_path = "/test/plan.yaml"
        context.filter_plan = None
        context.filter_suite = None
        context.filter_case = None
        context.plugin_manager = MagicMock()
        context.plugin_manager.get_collector_plugins.return_value = {}
        return context

    @pytest.fixture
    def basic_yaml_content(self):
        return """
        version: "1.0"
        plans:
          - name: plan1
            config:
              replication: 2
              params:
                key_a: value_a
            suites:
              - name: suite1
                config:
                  replication: 2
                  concurrency: true
                  params:
                    key_b: value_b
                cases:
                  - name: case1
                    config:
                      replication: 2
                      parallelism: 3
                      params:
                        key_c: value_c
                    commands:
                      - cmd: "echo 'test'"
                        shell: true
        """

    def test_init(self, context):
        parser = Parser(context)
        assert parser.context == context
        assert parser._plans == []
        assert parser._validator is not None

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pymergen.core.parser.Parser._validate_document')
    def test_load_file(self, mock_validate, mock_yaml_load, mock_file, mock_isfile, mock_isdir, context):
        # Setup
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        mock_yaml_load.return_value = {"version": "1.0", "plans": [{"name": "test_plan"}]}

        # Execute
        parser = Parser(context)
        parser.load()

        # Assert
        mock_file.assert_called_once_with("/test/plan.yaml", "r")
        mock_yaml_load.assert_called_once()
        mock_validate.assert_called_once()
        assert parser._plans == [{"name": "test_plan"}]

    @patch('os.path.isdir')
    @patch('glob.glob')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pymergen.core.parser.Parser._validate_document')
    def test_load_directory(self, mock_validate, mock_yaml_load, mock_file, mock_glob, mock_isdir, context):
        # Setup
        mock_isdir.return_value = True
        mock_glob.return_value = ["/test/plan1.yaml", "/test/plan2.yaml"]
        mock_yaml_load.side_effect = [
            {"version": "1.0", "plans": [{"name": "plan1"}]},
            {"version": "1.0", "plans": [{"name": "plan2"}]}
        ]

        # Execute
        parser = Parser(context)
        parser.load()

        # Assert
        assert mock_file.call_count == 2
        assert mock_yaml_load.call_count == 2
        assert mock_validate.call_count == 2
        assert parser._plans == [{"name": "plan1"}, {"name": "plan2"}]

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_parse_plan(self, mock_yaml_load, mock_file, context, basic_yaml_content):
        # Setup
        mock_yaml_load.return_value = {"version": "1.0", "plans": [{"name": "plan1"}]}
        parser = Parser(context)
        parser._plans = [{"name": "plan1"}]

        # Mock the _parse_plan method to return a known EntityPlan
        with patch.object(Parser, '_parse_plan') as mock_parse_plan:
            mock_plan = EntityPlan()
            mock_plan.name = "plan1"
            mock_parse_plan.return_value = mock_plan

            # Execute
            plans = parser.parse()

            # Assert
            assert len(plans) == 1
            assert plans[0].name == "plan1"
            mock_parse_plan.assert_called_once_with({"name": "plan1"})

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_parse_with_filter_plan(self, mock_yaml_load, mock_file, context):
        # Setup
        context.filter_plan = "plan1"
        mock_yaml_load.return_value = {"version": "1.0", "plans": [
            {"name": "plan1"}, 
            {"name": "plan2"}
        ]}

        parser = Parser(context)
        parser._plans = [{"name": "plan1"}, {"name": "plan2"}]

        # Create mock plans
        plan1 = EntityPlan()
        plan1.name = "plan1"
        plan2 = EntityPlan()
        plan2.name = "plan2"

        # Mock the _parse_plan method to return our EntityPlans
        with patch.object(Parser, '_parse_plan') as mock_parse_plan:
            mock_parse_plan.side_effect = [plan1, plan2]

            # Execute
            plans = parser.parse()

            # Assert
            assert len(plans) == 1
            assert plans[0].name == "plan1"
            assert mock_parse_plan.call_count == 2

    def test_parse_commands(self, context):
        # Setup
        parser = Parser(context)
        command_data = [
            {"name": "test1", "cmd": "echo 'test1'", "shell": True, "debug_stdout": True},
            {"name": "test2", "cmd": "echo 'test2'", "become_cmd": "sudo", "timeout": 30}
        ]

        # Execute
        commands = parser._parse_commands(command_data)

        # Assert
        assert len(commands) == 2
        assert commands[0].name == "test1"
        assert commands[0].cmd == "echo 'test1'"
        assert commands[0].shell is True
        assert commands[0].debug_stdout is True
        assert commands[0].become_cmd is None

        assert commands[1].name == "test2"
        assert commands[1].cmd == "echo 'test2'"
        assert commands[1].become_cmd == "sudo"
        assert commands[1].timeout == 30
        assert commands[1].shell is False

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    @patch('os.path.dirname')
    def test_load_includes(self, mock_dirname, mock_exists, mock_yaml_load, mock_file, context):
        # Setup
        mock_dirname.return_value = "/test"
        mock_exists.return_value = True

        # Simulate nested YAML loading
        mock_yaml_load.return_value = {"included_value": "test"}

        # Execute
        parser = Parser(context)
        result = parser._load_includes({"include_key": "include:included.yaml"}, "/test")

        # Assert
        assert result == {"include_key": {"included_value": "test"}}
        mock_file.assert_called_with("/test/included.yaml", "r")

    @patch('os.path.exists')
    def test_get_include_path(self, mock_exists, context):
        # Setup
        mock_exists.return_value = True
        parser = Parser(context)

        # Execute
        path = parser._get_include_path("include:test.yaml", "/base/dir")

        # Assert
        assert path == "/base/dir/test.yaml"
        mock_exists.assert_called_once_with("/base/dir/test.yaml")

    @patch('os.path.exists')
    def test_get_include_path_not_exists(self, mock_exists, context):
        # Setup
        mock_exists.return_value = False
        parser = Parser(context)

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser._get_include_path("include:test.yaml", "/base/dir")
        assert "Failed to load include at /base/dir/test.yaml" in str(excinfo.value)

    def test_parse_plan_method(self, context):
        # Setup
        parser = Parser(context)
        plan_data = {
            "name": "test_plan",
            "config": {
                "replication": 3,
                "params": {"key1": "value1"},
                "iters": {"iter1": ["a", "b"]}
            },
            "pre": [{"cmd": "echo pre"}],
            "post": [{"cmd": "echo post"}],
            "cgroups": [{
                "name": "test_cgroup",
                "controllers": [{"name": "cpu", "limits": [{"key": "cpu.shares", "value": "1024"}]}]
            }],
            "collectors": [{"engine": "process", "name": "test_collector"}],
            "suites": [{"name": "test_suite", "cases": [{"name": "test_case", "commands": [{"cmd": "echo test"}]}]}]
        }

        # Mock _parse_suite and _parse_cgroups and _parse_collectors
        with patch.object(Parser, '_parse_suite') as mock_parse_suite, \
             patch.object(Parser, '_parse_cgroups') as mock_parse_cgroups, \
             patch.object(Parser, '_parse_collectors') as mock_parse_collectors, \
             patch.object(Parser, '_parse_commands') as mock_parse_commands:

            # Setup return values
            mock_suite = EntitySuite()
            mock_suite.name = "test_suite"
            mock_parse_suite.return_value = mock_suite

            mock_cgroups = [MagicMock()]
            mock_parse_cgroups.return_value = mock_cgroups

            mock_collectors = [MagicMock()]
            mock_parse_collectors.return_value = mock_collectors

            mock_pre_commands = [MagicMock()]
            mock_post_commands = [MagicMock()]
            mock_parse_commands.side_effect = [mock_pre_commands, mock_post_commands]

            # Execute
            plan = parser._parse_plan(plan_data)

            # Assert
            assert isinstance(plan, EntityPlan)
            assert plan.name == "test_plan"
            assert plan.config.replication == 3
            assert plan.config.params == {"key1": "value1"}
            assert plan.config.iters == {"iter1": ["a", "b"]}
            assert plan.pre == mock_pre_commands
            assert plan.post == mock_post_commands
            assert plan.cgroups == mock_cgroups
            assert plan.collectors == mock_collectors
            assert len(plan.suites) == 1
            assert plan.suites[0] == mock_suite
            assert mock_suite.parent == plan

            # Verify method calls
            mock_parse_commands.assert_any_call([{"cmd": "echo pre"}])
            mock_parse_commands.assert_any_call([{"cmd": "echo post"}])
            mock_parse_cgroups.assert_called_once_with([{
                "name": "test_cgroup",
                "controllers": [{"name": "cpu", "limits": [{"key": "cpu.shares", "value": "1024"}]}]
            }])
            mock_parse_collectors.assert_called_once_with([{"engine": "process", "name": "test_collector"}])
            mock_parse_suite.assert_called_once()

    def test_parse_suite_method(self, context):
        # Setup
        parser = Parser(context)
        suite_data = {
            "name": "test_suite",
            "config": {
                "replication": 2,
                "concurrency": True,
                "params": {"key1": "value1"},
                "iters": {"iter1": ["a", "b"]}
            },
            "pre": [{"cmd": "echo suite pre"}],
            "post": [{"cmd": "echo suite post"}],
            "cases": [{"name": "test_case", "commands": [{"cmd": "echo test"}]}]
        }

        # Mock _parse_case and _parse_commands
        with patch.object(Parser, '_parse_case') as mock_parse_case, \
             patch.object(Parser, '_parse_commands') as mock_parse_commands:

            # Setup return values
            mock_case = EntityCase()
            mock_case.name = "test_case"
            mock_parse_case.return_value = mock_case

            mock_pre_commands = [MagicMock()]
            mock_post_commands = [MagicMock()]
            mock_parse_commands.side_effect = [mock_pre_commands, mock_post_commands]

            # Execute
            suite = parser._parse_suite(suite_data)

            # Assert
            assert isinstance(suite, EntitySuite)
            assert suite.name == "test_suite"
            assert suite.config.replication == 2
            assert suite.config.concurrency is True
            assert suite.config.params == {"key1": "value1"}
            assert suite.config.iters == {"iter1": ["a", "b"]}
            assert suite.pre == mock_pre_commands
            assert suite.post == mock_post_commands
            assert len(suite.cases) == 1
            assert suite.cases[0] == mock_case
            assert mock_case.parent == suite

            # Verify method calls
            mock_parse_commands.assert_any_call([{"cmd": "echo suite pre"}])
            mock_parse_commands.assert_any_call([{"cmd": "echo suite post"}])
            mock_parse_case.assert_called_once()

    def test_parse_case_method(self, context):
        # Setup
        parser = Parser(context)
        case_data = {
            "name": "test_case",
            "config": {
                "replication": 2,
                "parallelism": 3,
                "params": {"key1": "value1"},
                "iters": {"iter1": ["a", "b"]}
            },
            "pre": [{"cmd": "echo case pre"}],
            "post": [{"cmd": "echo case post"}],
            "commands": [{"cmd": "echo test command"}]
        }

        # Mock _parse_commands
        with patch.object(Parser, '_parse_commands') as mock_parse_commands:

            # Setup return values
            mock_pre_commands = [MagicMock()]
            mock_post_commands = [MagicMock()]
            mock_case_commands = [MagicMock()]
            mock_parse_commands.side_effect = [mock_pre_commands, mock_post_commands, mock_case_commands]

            # Execute
            case = parser._parse_case(case_data)

            # Assert
            assert isinstance(case, EntityCase)
            assert case.name == "test_case"
            assert case.config.replication == 2
            assert case.config.parallelism == 3
            assert case.config.params == {"key1": "value1"}
            assert case.config.iters == {"iter1": ["a", "b"]}
            assert case.pre == mock_pre_commands
            assert case.post == mock_post_commands
            assert case.commands == mock_case_commands

            # Verify method calls
            mock_parse_commands.assert_any_call([{"cmd": "echo case pre"}])
            mock_parse_commands.assert_any_call([{"cmd": "echo case post"}])
            mock_parse_commands.assert_any_call([{"cmd": "echo test command"}])

    @patch('pymergen.controller.factory.ControllerFactory.instance')
    def test_parse_cgroups(self, mock_controller_factory, context):
        # Setup
        parser = Parser(context)
        cgroup_data = [
            {
                "name": "test_cgroup",
                "become_cmd": "sudo -u root",
                "controllers": [
                    {
                        "name": "cpu", 
                        "limits": [
                            {"key": "cpu.shares", "value": "1024"},
                            {"key": "cpu.cfs_quota_us", "value": "50000"}
                        ]
                    },
                    {
                        "name": "memory",
                        "limits": [
                            {"key": "memory.limit_in_bytes", "value": "1G"}
                        ]
                    }
                ]
            }
        ]

        # Setup mocks
        mock_cpu_controller = MagicMock()
        mock_memory_controller = MagicMock()
        mock_controller_factory.side_effect = [mock_cpu_controller, mock_memory_controller]

        # Execute
        cgroups = parser._parse_cgroups(cgroup_data)

        # Assert
        assert len(cgroups) == 1
        cgroup = cgroups[0]
        assert cgroup.name == "test_cgroup"
        assert cgroup.become_cmd == "sudo -u root"

        # Verify controller factory calls
        mock_controller_factory.assert_any_call("cpu")
        mock_controller_factory.assert_any_call("memory")

        # Verify controller limits were added
        mock_cpu_controller.add_limit.assert_any_call("cpu.shares", "1024")
        mock_cpu_controller.add_limit.assert_any_call("cpu.cfs_quota_us", "50000")
        mock_memory_controller.add_limit.assert_called_once_with("memory.limit_in_bytes", "1G")

    def test_parse_collectors(self, context):
        # Setup
        parser = Parser(context)
        collector_data = [
            {"engine": "process", "name": "test_collector", "cmd": "collect data"},
            {"engine": "thread", "name": "thread_collector", "interval": 10}
        ]

        # Setup mocks
        mock_process_plugin = MagicMock()
        mock_thread_plugin = MagicMock()
        mock_process_collector = MagicMock()
        mock_thread_collector = MagicMock()

        mock_process_plugin.implementation.return_value = mock_process_collector
        mock_thread_plugin.implementation.return_value = mock_thread_collector

        context.plugin_manager.get_collector_plugin.side_effect = [mock_process_plugin, mock_thread_plugin]

        # Execute
        collectors = parser._parse_collectors(collector_data)

        # Assert
        assert len(collectors) == 2
        assert collectors[0] == mock_process_collector
        assert collectors[1] == mock_thread_collector

        # Verify plugin manager calls
        context.plugin_manager.get_collector_plugin.assert_any_call("process")
        context.plugin_manager.get_collector_plugin.assert_any_call("thread")

        # Verify implementation calls
        mock_process_plugin.implementation.assert_called_once_with({"engine": "process", "name": "test_collector", "cmd": "collect data"})
        mock_thread_plugin.implementation.assert_called_once_with({"engine": "thread", "name": "thread_collector", "interval": 10})

        # Verify context was set
        assert mock_process_collector.context == context
        assert mock_thread_collector.context == context

    @patch('importlib.import_module')
    def test_init_validator_success(self, mock_import_module, context):
        # Setup
        mock_import_module.return_value = MagicMock()

        # Execute
        parser = Parser(context)

        # Assert
        mock_import_module.assert_called_once_with("cerberus")
        assert parser._validator is not None

    @patch('importlib.import_module')
    def test_init_validator_module_not_found(self, mock_import_module, context):
        # Setup
        mock_import_module.side_effect = ModuleNotFoundError("No module named 'cerberus'")

        # Execute
        parser = Parser(context)

        # Assert
        mock_import_module.assert_called_once_with("cerberus")
        assert parser._validator is None
        context.logger.warning.assert_called_once_with("Unable to load module cerberus")

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    @patch('os.path.dirname')
    @patch('pprint.pprint')
    @patch('pprint.pformat')
    def test_validate_document_errors(self, mock_pformat, mock_pprint, mock_dirname, 
                                    mock_exists, mock_yaml_load, mock_file, context):
        # Setup
        mock_dirname.return_value = "/test"
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "plans": {
                "schema": {
                    "schema": {
                        "collectors": {
                            "schema": {
                                "anyof": []
                            }
                        }
                    }
                }
            }
        }

        mock_validator = MagicMock()
        mock_validator.validate.return_value = False
        mock_validator.errors = {"plans": ["must be of list type"]}
        mock_pformat.return_value = "{'plans': ['must be of list type']}"

        parser = Parser(context)
        parser._validator = mock_validator

        document = {"version": "1.0", "plans": "not a list"}

        # Setup empty collector plugins
        context.plugin_manager.get_collector_plugins.return_value = {}

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser._validate_document(document, "/test/plan.yaml")

        assert "Failed to validate document /test/plan.yaml due to" in str(excinfo.value)
        mock_pprint.assert_any_call(document)
        mock_pprint.assert_any_call(mock_validator.errors)
        mock_pformat.assert_called_once_with(mock_validator.errors)

    def test_validate_document_no_version(self, context):
        # Setup
        parser = Parser(context)
        parser._validator = MagicMock()
        document = {"plans": []}

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser._validate_document(document, "/test/plan.yaml")

        assert "Document does not have a version defined" in str(excinfo.value)

    @patch('os.path.exists')
    @patch('os.path.dirname')
    def test_validate_document_schema_not_exists(self, mock_dirname, mock_exists, context):
        # Setup
        mock_dirname.return_value = "/test"
        mock_exists.return_value = False

        parser = Parser(context)
        parser._validator = MagicMock()
        document = {"version": "1.0", "plans": []}

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser._validate_document(document, "/test/plan.yaml")

        assert "Schema path /test/../conf/schema/schema_1.0.yaml does not exist" in str(excinfo.value)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_load_file_not_yaml(self, mock_isfile, mock_isdir, mock_yaml_load, mock_file, context):
        # Setup
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        context.plan_path = "/test/plan.txt"  # Not a yaml file

        parser = Parser(context)

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser.load()

        assert "Only YAML files are supported" in str(excinfo.value)
        assert not mock_yaml_load.called

    @patch('os.path.isdir')
    @patch('glob.glob')
    def test_load_directory_empty(self, mock_glob, mock_isdir, context):
        # Setup
        mock_isdir.return_value = True
        mock_glob.return_value = []  # No yaml files

        parser = Parser(context)

        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            parser.load()

        assert f"No YAML files are found in {context.plan_path}" in str(excinfo.value)

    def test_load_includes_with_nested_structures(self, context):
        # Setup
        parser = Parser(context)

        with patch.object(Parser, '_load_yaml') as mock_load_yaml, \
             patch.object(Parser, '_get_include_path') as mock_get_include_path:

            # Define mock implementations
            def mock_load_yaml_impl(path):
                if path == "/base/included1.yaml":
                    return {"key1": "value1"}
                elif path == "/base/included2.yaml":
                    return {"key2": "value2"}
                elif path == "/base/nested.yaml":
                    return [1, 2, 3]

            mock_load_yaml.side_effect = mock_load_yaml_impl

            def mock_get_include_path_impl(value, base_dir):
                if value == "include:included1.yaml":
                    return "/base/included1.yaml"
                elif value == "include:included2.yaml":
                    return "/base/included2.yaml"
                elif value == "include:nested.yaml":
                    return "/base/nested.yaml"

            mock_get_include_path.side_effect = mock_get_include_path_impl

            # Test with different data structures
            # 1. Simple string include
            result1 = parser._load_includes("include:included1.yaml", "/base")
            assert result1 == {"key1": "value1"}

            # 2. List with includes
            result2 = parser._load_includes(["normal", "include:included1.yaml", "include:nested.yaml"], "/base")
            assert result2 == ["normal", {"key1": "value1"}, [1, 2, 3]]

            # 3. Dict with includes
            result3 = parser._load_includes({
                "normal_key": "normal_value",
                "include_key": "include:included1.yaml",
                "nested": {
                    "include_key": "include:included2.yaml"
                }
            }, "/base")

            assert result3 == {
                "normal_key": "normal_value",
                "include_key": {"key1": "value1"},
                "nested": {
                    "include_key": {"key2": "value2"}
                }
            }
