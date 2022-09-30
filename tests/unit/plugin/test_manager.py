import pytest
import os
import glob
from unittest.mock import MagicMock, patch, call
from pymergen.plugin.manager import PluginManager
from pymergen.plugin.registry import PluginRegistry
from pymergen.plugin.plugin import Plugin


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.plugin_path = "/test/plugin/path"
    return context


class TestPluginManager:
    def test_plugin_manager_init(self, mock_context):
        """Test plugin manager initialization"""
        manager = PluginManager(mock_context)

        assert manager._context == mock_context
        assert manager._paths is None
        assert isinstance(manager._registry, PluginRegistry)
        assert PluginManager.CATEGORY_COLLECTOR in manager._registry.categories

    def test_paths_property(self, mock_context):
        """Test paths property"""
        manager = PluginManager(mock_context)
        paths = manager.paths

        # Should have plugin directory and custom path from context
        assert len(paths) == 2
        assert os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pymergen/plugin')) in paths
        assert mock_context.plugin_path in paths

        # Test caching
        assert manager._paths is paths

        # Test when context.plugin_path is None
        mock_context.plugin_path = None
        manager = PluginManager(mock_context)
        paths = manager.paths

        assert len(paths) == 1
        assert os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pymergen/plugin')) in paths

    def test_registry_property(self, mock_context):
        """Test registry property"""
        manager = PluginManager(mock_context)
        registry = manager.registry

        assert isinstance(registry, PluginRegistry)
        assert registry == manager._registry

    @patch('glob.glob')
    @patch('importlib.machinery.SourceFileLoader')
    @patch('importlib.util.spec_from_loader')
    @patch('importlib.util.module_from_spec')
    def test_load(self, mock_module_from_spec, mock_spec_from_loader, 
                  mock_loader, mock_glob, mock_context):
        """Test plugin loading"""
        # Setup mocks
        mock_glob.return_value = ["/test/path/collector/test_plugin/plugin.py"]

        mock_loader_instance = MagicMock()
        mock_loader.return_value = mock_loader_instance

        mock_spec = MagicMock()
        mock_spec_from_loader.return_value = mock_spec

        mock_module = MagicMock()
        mock_plugin = MagicMock(spec=Plugin)
        mock_plugin.engine = "test_engine"
        mock_module.Plugin.return_value = mock_plugin
        mock_module_from_spec.return_value = mock_module

        # Execute
        manager = PluginManager(mock_context)
        with patch.object(manager, '_paths', ['/test/path']):
            manager.load()

        # Verify
        mock_glob.assert_called_with(os.path.join('/test/path', 'collector', '*', 'plugin.py'))
        mock_loader.assert_called_with('collector', '/test/path/collector/test_plugin/plugin.py')
        mock_spec_from_loader.assert_called_with(mock_loader_instance.name, mock_loader_instance)
        mock_module_from_spec.assert_called_with(mock_spec)
        mock_loader_instance.exec_module.assert_called_with(mock_module)

        # Verify plugin was added to registry
        mock_plugin = manager._registry.get_plugin(PluginManager.CATEGORY_COLLECTOR, "test_engine")
        assert mock_plugin == mock_module.Plugin.return_value

    def test_get_collector_plugin(self, mock_context):
        """Test get_collector_plugin method"""
        manager = PluginManager(mock_context)

        # Mock registry.get_plugin
        mock_plugin = MagicMock(spec=Plugin)
        manager._registry.get_plugin = MagicMock(return_value=mock_plugin)

        result = manager.get_collector_plugin("test_engine")

        # Verify
        manager._registry.get_plugin.assert_called_with(PluginManager.CATEGORY_COLLECTOR, "test_engine")
        assert result == mock_plugin

    def test_get_collector_plugins(self, mock_context):
        """Test get_collector_plugins method"""
        manager = PluginManager(mock_context)

        # Mock registry.get_plugins
        mock_plugins = {"engine1": MagicMock(), "engine2": MagicMock()}
        manager._registry.get_plugins = MagicMock(return_value=mock_plugins)

        result = manager.get_collector_plugins()

        # Verify
        manager._registry.get_plugins.assert_called_with(PluginManager.CATEGORY_COLLECTOR)
        assert result == mock_plugins
