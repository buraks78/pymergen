import pytest
from unittest.mock import MagicMock, patch
from pymergen.plugin.manager import PluginManager
from pymergen.plugin.registry import PluginRegistry
from pymergen.plugin.plugin import Plugin
from pymergen.collector.collector import Collector


class MockCollectorPlugin(Plugin):
    def __init__(self, engine_name="test_engine"):
        super().__init__()
        self._engine_name = engine_name
        self._context = None

    @property
    def engine(self) -> str:
        return self._engine_name

    def schema(self, version: str) -> dict:
        return {"version": version, "type": "collector"}

    def implementation(self, config: dict) -> Collector:
        collector = MagicMock(spec=Collector)
        collector.name = "test_collector"
        collector.context = self._context
        return collector


class TestPluginCollectorIntegration:
    @patch('importlib.machinery.SourceFileLoader')
    @patch('importlib.util.spec_from_loader')
    @patch('importlib.util.module_from_spec')
    @patch('glob.glob')
    def test_plugin_collector_integration(self, mock_glob, 
                                          mock_module_from_spec,
                                          mock_spec_from_loader,
                                          mock_loader):
        """Test integration between PluginManager and collector plugins"""
        # Setup mocks
        mock_context = MagicMock()
        mock_context.plugin_path = None

        # Setup plugin loading mocks
        mock_glob.return_value = ["/path/to/collector/test_engine/plugin.py"]

        mock_loader_instance = MagicMock()
        mock_loader.return_value = mock_loader_instance

        mock_spec = MagicMock()
        mock_spec_from_loader.return_value = mock_spec

        mock_module = MagicMock()
        mock_plugin = MockCollectorPlugin()
        mock_module.Plugin = lambda: mock_plugin
        mock_module_from_spec.return_value = mock_module

        # Create plugin manager
        manager = PluginManager(mock_context)

        # Make the plugin discoverable via mocks
        with patch.object(manager, '_paths', ['/path/to']):
            manager.load()

        # Get the collector plugin
        plugin = manager.get_collector_plugin("test_engine")
        assert plugin is not None
        assert plugin.engine == "test_engine"

        # Test creating a collector implementation
        collector = plugin.implementation({"name": "test_collector"})
        assert collector is not None
        assert collector.name == "test_collector"

        # Test getting all collector plugins
        plugins = manager.get_collector_plugins()
        assert "test_engine" in plugins
        assert plugins["test_engine"] == plugin

    def test_multiple_collector_plugins(self):
        """Test registry with multiple collector plugins"""
        # Create registry and add collector category
        registry = PluginRegistry()
        registry.add_category(PluginManager.CATEGORY_COLLECTOR)

        # Create mock plugins
        plugin1 = MockCollectorPlugin("engine1")
        plugin2 = MockCollectorPlugin("engine2")
        plugin3 = MockCollectorPlugin("engine3")

        # Register plugins
        registry.add_plugin(PluginManager.CATEGORY_COLLECTOR, plugin1.engine, plugin1)
        registry.add_plugin(PluginManager.CATEGORY_COLLECTOR, plugin2.engine, plugin2)
        registry.add_plugin(PluginManager.CATEGORY_COLLECTOR, plugin3.engine, plugin3)

        # Get all plugins
        plugins = registry.get_plugins(PluginManager.CATEGORY_COLLECTOR)

        # Verify all plugins are registered
        assert len(plugins) == 3
        assert plugins["engine1"] == plugin1
        assert plugins["engine2"] == plugin2
        assert plugins["engine3"] == plugin3

        # Get specific plugin
        plugin = registry.get_plugin(PluginManager.CATEGORY_COLLECTOR, "engine2")
        assert plugin == plugin2
