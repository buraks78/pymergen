import pytest
from unittest.mock import MagicMock
from pymergen.plugin.plugin import Plugin
from pymergen.plugin.registry import PluginRegistry
from pymergen.plugin.manager import PluginManager


@pytest.fixture
def mock_plugin():
    """Return a mock plugin"""
    plugin = MagicMock(spec=Plugin)
    plugin.engine = "test_engine"
    return plugin


@pytest.fixture
def registry():
    """Return a fresh PluginRegistry instance"""
    return PluginRegistry()


@pytest.fixture
def mock_context():
    """Return a mock context"""
    context = MagicMock()
    context.plugin_path = "/test/plugin/path"
    context.logger = MagicMock()
    return context


@pytest.fixture
def plugin_manager(mock_context):
    """Return a PluginManager with mocked context"""
    return PluginManager(mock_context)
