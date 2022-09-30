import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pymergen.core.stat import StatTimer, Stat


class TestStatTimer:
    def test_init(self):
        """Test timer initialization"""
        timer = StatTimer()
        assert timer._active is False
        assert timer._started_at is None
        assert timer._stopped_at is None
        assert timer._duration is None

    def test_properties(self):
        """Test property getters"""
        timer = StatTimer()
        timer._started_at = 100.0
        timer._stopped_at = 105.0

        assert timer.started_at == 100.0
        assert timer.stopped_at == 105.0

    def test_duration_calculation(self):
        """Test duration property calculates and rounds correctly"""
        timer = StatTimer()
        timer._started_at = 100.0
        timer._stopped_at = 105.123456

        # First call calculates duration
        assert timer.duration == 5.12
        # Second call uses cached value
        assert timer.duration == 5.12
        # Verify duration was cached
        assert timer._duration == 5.12

    def test_start(self):
        """Test start method sets timer state"""
        timer = StatTimer()

        with patch('time.time', return_value=100.5):
            timer.start()

        assert timer._active is True
        assert timer._started_at == 100.5

    def test_start_raises_exception_when_active(self):
        """Test start raises exception when timer is already active"""
        timer = StatTimer()
        timer._active = True

        with pytest.raises(Exception) as excinfo:
            timer.start()

        assert "Timer is already active" in str(excinfo.value)

    def test_stop(self):
        """Test stop method sets timer state"""
        timer = StatTimer()
        timer._active = True

        with patch('time.time', return_value=105.5):
            timer.stop()

        assert timer._active is False
        assert timer._stopped_at == 105.5

    def test_stop_raises_exception_when_inactive(self):
        """Test stop raises exception when timer is not active"""
        timer = StatTimer()
        timer._active = False

        with pytest.raises(Exception) as excinfo:
            timer.stop()

        assert "Timer is not active" in str(excinfo.value)

    def test_log(self):
        """Test log method writes timer data to file"""
        timer = StatTimer()
        timer._started_at = 100.0
        timer._stopped_at = 105.0

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('json.dumps', return_value='{\'mocked_json\': true}'):
                timer.log(temp_dir)

            # Verify file was created with expected content
            log_file_path = os.path.join(temp_dir, "stat.timer.json")
            assert os.path.exists(log_file_path)

            with open(log_file_path, 'r') as f:
                content = f.read()
                assert content == "{data}\n".format(data='{\'mocked_json\': true}')


class TestStat:
    def test_init(self):
        """Test Stat initialization creates StatTimer"""
        stat = Stat()
        assert isinstance(stat._timer, StatTimer)

    def test_timer_property(self):
        """Test timer property returns the StatTimer instance"""
        stat = Stat()
        timer = stat.timer
        assert timer is stat._timer

    @patch.object(StatTimer, 'start')
    def test_start(self, mock_start):
        """Test start delegates to timer.start"""
        stat = Stat()
        stat.start()
        mock_start.assert_called_once()

    @patch.object(StatTimer, 'stop')
    def test_stop(self, mock_stop):
        """Test stop delegates to timer.stop"""
        stat = Stat()
        stat.stop()
        mock_stop.assert_called_once()

    @patch.object(StatTimer, 'log')
    def test_log(self, mock_log):
        """Test log delegates to timer.log"""
        stat = Stat()
        stat.log("/test/path")
        mock_log.assert_called_once_with("/test/path")
