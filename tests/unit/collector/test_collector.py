import pytest
from unittest.mock import MagicMock, patch
from pymergen.collector.collector import Collector
from pymergen.core.context import Context


class TestCollector:
    def test_init(self):
        """Test collector initialization"""
        collector = Collector()
        assert collector._name is None
        assert collector._context is None

    def test_parse(self):
        """Test parsing configuration"""
        collector = Collector()
        config = {"name": "test_collector"}
        collector.parse(config)
        assert collector.name == "test_collector"

    def test_name_property(self):
        """Test name property getter and setter"""
        collector = Collector()
        assert collector.name is None

        collector.name = "test_name"
        assert collector.name == "test_name"

    def test_context_property(self):
        """Test context property getter and setter"""
        collector = Collector()
        assert collector.context is None

        # Use MagicMock instead of actual Context
        context = MagicMock(spec=Context)
        collector.context = context
        assert collector.context is context

    def test_configure(self):
        """Test configure method"""
        collector = Collector()
        # The base configure method should do nothing
        collector.configure({"some": "config"})
        # No assertion needed, just verifying it doesn't raise an exception

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError"""
        collector = Collector()
        with pytest.raises(NotImplementedError):
            collector.start(MagicMock())

        with pytest.raises(NotImplementedError):
            collector.stop()