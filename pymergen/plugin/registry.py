from typing import List, Dict
from collections import defaultdict
from pymergen.plugin.plugin import Plugin


class PluginRegistry:

    def __init__(self):
        self._categories = list()
        self._plugins = defaultdict(dict)

    @property
    def categories(self) -> List:
        return self._categories

    @categories.setter
    def categories(self, values: List[str]) -> None:
        self._categories = values

    def add_category(self, value: str) -> None:
        self._categories.append(value)

    def add_plugin(self, category: str, engine: str, plugin: Plugin):
        self._check_category(category)
        self._plugins[category][engine] = plugin

    def get_plugin(self, category: str, engine: str) -> Plugin:
        self._check_category(category)
        return self._plugins.get(category).get(engine)

    def get_plugins(self, category: str) -> Dict[str, Plugin]:
        self._check_category(category)
        return self._plugins.get(category)

    def _check_category(self, category: str) -> None:
        if category not in self._categories:
            raise Exception("Plugin category {category} is not recognized".format(category=category))
