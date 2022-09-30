import os
import sys
import pytest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime
from pymergen.core.context import Context


class TestContext:
    @pytest.fixture
    def args(self):
        args = MagicMock()
        args.plan_path = "/test/plan.yaml"
        args.work_path = "/test/work"
        args.plugin_path = "/test/plugins"
        args.log_level = "INFO"
        args.filter_plan = None
        args.filter_suite = None
        args.filter_case = None
        return args

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.mkdir')
    @patch('pymergen.core.context.Logger.logger')
    def test_init(self, mock_logger, mock_mkdir, mock_isdir, mock_exists, args):

        mock_isdir.return_value = False
        mock_logger.return_value = MagicMock()
        mock_logger.return_value.handlers = [logging.StreamHandler()]

        with patch('pymergen.core.context.Context._generate_run_path') as mock_generate_path:

            mock_generate_path.return_value = "20230101_120000"
            # Execute
            context = Context(args)

            # Assert
            assert context.plan_path == "/test/plan.yaml"
            assert context.work_path == "/test/work"
            assert context.plugin_path == "/test/plugins"
            assert context.run_path == "/test/work/20230101_120000"
            assert context.log_level == "INFO"
            assert context.filter_plan is None
            assert context.filter_suite is None
            assert context.filter_case is None
            mock_mkdir.assert_any_call("/test/work")
            mock_mkdir.assert_any_call("/test/work/20230101_120000")

    def test_plugin_manager_property_lazy_loading(self, args):
        with patch('pymergen.core.context.Context._prepare'), \
             patch('pymergen.core.context.Context._init_logger'), \
             patch('pymergen.core.context.PluginManager') as mock_plugin_manager_class:
            mock_plugin_manager = MagicMock()
            mock_plugin_manager_class.return_value = mock_plugin_manager

            context = Context(args)
            # First access should create the plugin manager
            assert context.plugin_manager is mock_plugin_manager
            mock_plugin_manager_class.assert_called_once_with(context)
            mock_plugin_manager.load.assert_called_once()

            # Second access should return the same instance
            mock_plugin_manager_class.reset_mock()
            mock_plugin_manager.reset_mock()
            assert context.plugin_manager is mock_plugin_manager
            mock_plugin_manager_class.assert_not_called()
            mock_plugin_manager.load.assert_not_called()

    @patch('sys.platform', 'linux')
    @patch('shutil.which')
    @patch('os.path.exists')
    def test_validate_success(self, mock_exists, mock_which, args):
        # Setup
        mock_which.return_value = "/usr/bin/command"
        mock_exists.return_value = True

        with patch('pymergen.core.context.Context._prepare'), \
             patch('pymergen.core.context.Context._init_logger'):
            context = Context(args)
            # Should not raise exceptions
            context.validate()

    @patch('sys.platform', 'darwin')
    def test_validate_platform_error(self, args):
        with patch('pymergen.core.context.Context._prepare'), \
             patch('pymergen.core.context.Context._init_logger'):
            context = Context(args)
            with pytest.raises(Exception) as excinfo:
                context.validate()
            assert "Linux support only" in str(excinfo.value)

    @patch('sys.platform', 'linux')
    @patch('shutil.which')
    def test_validate_binary_not_found(self, mock_which, args):
        # Setup
        mock_which.return_value = None

        with patch('pymergen.core.context.Context._prepare'), \
             patch('pymergen.core.context.Context._init_logger'):
            context = Context(args)
            with pytest.raises(Exception) as excinfo:
                context.validate()
            assert "Command cgcreate not found" in str(excinfo.value)

    @patch('sys.platform', 'linux')
    @patch('shutil.which')
    @patch('os.path.exists')
    def test_validate_plan_path_not_exist(self, mock_exists, mock_which, args):
        # Setup
        mock_which.return_value = "/usr/bin/command"
        mock_exists.return_value = False

        with patch('pymergen.core.context.Context._prepare'), \
             patch('pymergen.core.context.Context._init_logger'):
            context = Context(args)
            with pytest.raises(Exception) as excinfo:
                context.validate()
            assert "Plan path /test/plan.yaml does not exist" in str(excinfo.value)
