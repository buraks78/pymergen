import os
import pytest
import logging
from unittest.mock import MagicMock, patch
from pymergen.core.logger import Logger


class TestLogger:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        Logger._logger = None

    @pytest.fixture
    def context(self):
        context = MagicMock()
        context.run_path = "/test/run"
        context.log_level = "INFO"
        return context

    @patch('logging.getLogger')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    def test_logger_initialization(self, mock_stream_handler,
                                 mock_file_handler, mock_get_logger, context):
        # Setup
        mock_logger = MagicMock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger
        mock_logger.handlers = []

        mock_stream_handler_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        mock_file_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_file_handler_instance

        logger = Logger.logger(context)

        # Assert
        mock_get_logger.assert_called_once_with("pymergen")
        assert logger == mock_logger
        # Should have at least 2 handlers (console and file)
        assert len(mock_logger.addHandler.call_args_list) >= 2

    @patch('logging.getLogger')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    @patch('logging.Formatter')
    def test_handlers_configuration(self, mock_formatter, mock_stream_handler, 
                                 mock_file_handler, mock_get_logger, context):

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance

        mock_stream_handler_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        mock_file_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_file_handler_instance

        logger = Logger.logger(context)

        # Assert
        # Verify logger level was set
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)

        # Verify console handler setup
        mock_stream_handler.assert_called_once()
        mock_stream_handler_instance.setLevel.assert_called_once()
        mock_stream_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        # Verify file handler setup
        mock_file_handler.assert_called_once_with(os.path.join(context.run_path, "run.runner.log"))
        mock_file_handler_instance.setLevel.assert_called_once()
        mock_file_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        # Verify handlers were added to logger
        assert mock_logger.addHandler.call_count >= 2
        mock_logger.addHandler.assert_any_call(mock_stream_handler_instance)
        mock_logger.addHandler.assert_any_call(mock_file_handler_instance)

    @patch('logging.getLogger')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    @patch('logging.Formatter')
    def test_logger_singleton(self, mock_formatter, mock_stream_handler,
                                 mock_file_handler, mock_get_logger, context):
        # Setup
        mock_logger1 = MagicMock()
        mock_logger1.handlers = [MagicMock()]  # Add a handler to avoid initialization
        mock_logger2 = MagicMock()
        mock_get_logger.side_effect = [mock_logger1, mock_logger2]

        # First call - should initialize logger
        logger1 = Logger.logger(context)

        # Reset mock to verify it's not called again
        mock_logger1.reset_mock()

        # Second call - should return the same logger without re-initializing
        logger2 = Logger.logger(context)

        # Assert
        assert logger1 == logger2  # Same logger instance
        # Handlers shouldn't be added again
        mock_logger1.addHandler.assert_not_called()
