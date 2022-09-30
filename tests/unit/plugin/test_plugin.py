import pytest
from typing import Dict, Any
from pymergen.plugin.plugin import Plugin


class TestPlugin:
    def test_plugin_init(self):
        """Test plugin initialization"""
        plugin = Plugin()
        assert plugin._engine is None

    def test_engine_property_not_implemented(self):
        """Test that engine property raises NotImplementedError"""
        plugin = Plugin()
        with pytest.raises(NotImplementedError):
            plugin.engine

    def test_schema_not_implemented(self):
        """Test that schema method raises NotImplementedError"""
        plugin = Plugin()
        with pytest.raises(NotImplementedError):
            plugin.schema("1.0")

    def test_implementation_not_implemented(self):
        """Test that implementation method raises NotImplementedError"""
        plugin = Plugin()
        with pytest.raises(NotImplementedError):
            plugin.implementation({})

    def test_concrete_plugin_implementation(self):
        """Test a concrete implementation of Plugin"""
        class ConcretePlugin(Plugin):
            @property
            def engine(self) -> str:
                return "test_engine"

            def schema(self, version: str) -> Dict:
                return {"version": version, "type": "test"}

            def implementation(self, config: Dict) -> Any:
                return "test_implementation"

        plugin = ConcretePlugin()
        assert plugin.engine == "test_engine"
        assert plugin.schema("1.0") == {"version": "1.0", "type": "test"}
        assert plugin.implementation({}) == "test_implementation"
