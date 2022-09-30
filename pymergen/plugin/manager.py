import os
import glob
from typing import List, Dict
import importlib.machinery
import importlib.util
from pymergen.plugin.registry import PluginRegistry
from pymergen.plugin.plugin import Plugin


class PluginManager:

    CATEGORY_COLLECTOR = "collector"

    def __init__(self, context):
        self._context = context
        self._paths = None
        self._init_registry()

    def _init_registry(self):
        self._registry = PluginRegistry()
        self._registry.add_category(self.CATEGORY_COLLECTOR)

    @property
    def paths(self) -> List:
        if self._paths is None:
            self._paths = list()
            self._paths.append(os.path.dirname(__file__))
            if self._context.plugin_path is not None:
                self._paths.append(self._context.plugin_path)
        return self._paths

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def load(self):
        for path in self.paths:
            for category in self._registry.categories:
                for plugin_file in glob.glob(os.path.join(path, category, '*', 'plugin.py')):
                    loader = importlib.machinery.SourceFileLoader(category, plugin_file)
                    plugin_spec = importlib.util.spec_from_loader(loader.name, loader)
                    plugin_module = importlib.util.module_from_spec(plugin_spec)
                    loader.exec_module(plugin_module)
                    plugin = plugin_module.Plugin()
                    self._registry.add_plugin(category, plugin.engine, plugin)

    def get_collector_plugin(self, engine: str) -> Plugin:
        return self._registry.get_plugin(self.CATEGORY_COLLECTOR, engine)

    def get_collector_plugins(self) -> Dict[str, Plugin]:
        return self._registry.get_plugins(self.CATEGORY_COLLECTOR)
