import pytest
from unittest.mock import MagicMock, patch
import threading
from pymergen.core.thread import Thread
from pymergen.core.context import Context


class TestThread:
    @pytest.fixture
    def context(self):
        context = MagicMock()
        context.logger = MagicMock()
        return context

    @pytest.fixture
    def thread(context):
        """Return a Thread instance with mock context"""
        return Thread(context)

    def test_init(self, context):
        thread = Thread(context)
        assert thread.context == context
        assert thread._thread is None

    @patch('threading.Thread')
    def test_thread_integration(self, mock_threading_class, context):
        args = [1, 2, 3]

        mock_threading_thread = MagicMock()
        mock_threading_class.return_value = mock_threading_thread

        mock_target = MagicMock()

        # Execute
        thread = Thread(context)
        thread.run(mock_target, args)
        thread.join()

        mock_threading_thread.start.assert_called_once()
        mock_threading_thread.join.assert_called_once()

    def test_target_integration(self, context):

        args = [1, 2, 3]

        mock_target = MagicMock()

        # Execute
        thread = Thread(context)
        thread.run(mock_target, args)
        thread.join()

        mock_target.run.assert_called_once_with(*args)

    def test_join_without_thread(self, thread):
        """Test join method when no thread exists"""
        # Thread is None initially
        assert thread._thread is None

        # Call join should raise AttributeError
        with pytest.raises(AttributeError):
            thread.join()
