from typing import Dict
from pymergen.plugin.plugin import Plugin as BasePlugin
from pymergen.collector.process import CollectorProcess


class Plugin(BasePlugin):

    @property
    def engine(self) -> str:
        return super()._engine(__file__)

    def schema(self, version: str) -> Dict:
        return super()._schema(__file__, version)

    def implementation(self, config: Dict) -> CollectorProcess:
        collector = CollectorProcess()
        collector.parse(config)
        return collector
