import pytest
from unittest.mock import MagicMock
from typing import Dict
from pymergen.plugin.registry import PluginRegistry
from pymergen.plugin.plugin import Plugin


class TestPluginRegistry:
    def test_registry_init(self):
        """Test registry initialization"""
        registry = PluginRegistry()
        assert registry._categories == []
        assert isinstance(registry._plugins, dict)
        assert len(registry._plugins) == 0

    def test_categories_property(self):
        """Test categories property getter and setter"""
        registry = PluginRegistry()
        assert registry.categories == []

        test_categories = ["cat1", "cat2"]
        registry.categories = test_categories

        assert registry.categories == test_categories

    def test_add_category(self):
        """Test adding categories to registry"""
        registry = PluginRegistry()
        registry.add_category("test_category")

        assert "test_category" in registry.categories
        assert len(registry.categories) == 1

        # Add another category
        registry.add_category("another_category")
        assert len(registry.categories) == 2
        assert "another_category" in registry.categories

    def test_add_plugin(self):
        """Test adding plugins to registry"""
        registry = PluginRegistry()
        registry.add_category("test_category")

        # Create mock plugin
        mock_plugin = MagicMock(spec=Plugin)

        # Add plugin
        registry.add_plugin("test_category", "test_engine", mock_plugin)

        # Verify plugin was added
        assert "test_engine" in registry._plugins["test_category"]
        assert registry._plugins["test_category"]["test_engine"] == mock_plugin

    def test_add_plugin_invalid_category(self):
        """Test adding plugin to invalid category"""
        registry = PluginRegistry()
        mock_plugin = MagicMock(spec=Plugin)

        with pytest.raises(Exception) as exc_info:
            registry.add_plugin("invalid_category", "test_engine", mock_plugin)

        assert "Plugin category invalid_category is not recognized" in str(exc_info.value)

    def test_get_plugin(self):
        """Test getting a plugin from registry"""
        registry = PluginRegistry()
        registry.add_category("test_category")

        # Create mock plugin
        mock_plugin = MagicMock(spec=Plugin)

        # Add plugin
        registry.add_plugin("test_category", "test_engine", mock_plugin)

        # Get plugin
        retrieved_plugin = registry.get_plugin("test_category", "test_engine")
        assert retrieved_plugin == mock_plugin

        # Test getting non-existent plugin
        non_existent = registry.get_plugin("test_category", "non_existent")
        assert non_existent is None

    def test_get_plugins(self):
        """Test getting all plugins for a category"""
        registry = PluginRegistry()
        registry.add_category("test_category")

        # Create mock plugins
        mock_plugin1 = MagicMock(spec=Plugin)
        mock_plugin2 = MagicMock(spec=Plugin)

        # Add plugins
        registry.add_plugin("test_category", "engine1", mock_plugin1)
        registry.add_plugin("test_category", "engine2", mock_plugin2)

        # Get all plugins
        plugins = registry.get_plugins("test_category")
        assert isinstance(plugins, Dict)
        assert len(plugins) == 2
        assert plugins["engine1"] == mock_plugin1
        assert plugins["engine2"] == mock_plugin2

    def test_get_plugins_invalid_category(self):
        """Test getting plugins from invalid category"""
        registry = PluginRegistry()

        with pytest.raises(Exception) as exc_info:
            registry.get_plugins("invalid_category")

        assert "Plugin category invalid_category is not recognized" in str(exc_info.value)

    def test_check_category(self):
        """Test _check_category method"""
        registry = PluginRegistry()
        registry.add_category("valid")

        # Valid category should not raise exception
        registry._check_category("valid")

        # Invalid category should raise exception
        with pytest.raises(Exception) as exc_info:
            registry._check_category("invalid")

        assert "Plugin category invalid is not recognized" in str(exc_info.value)
