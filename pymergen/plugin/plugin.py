import os
import yaml
from typing import Dict, Any


class Plugin:

    def __init__(self):
        self._engine = None

    @property
    def engine(self) -> str:
        raise NotImplementedError()

    def schema(self, version: str) -> Dict:
        raise NotImplementedError()

    def implementation(self, config: Dict) -> Any:
        raise NotImplementedError()

    def _engine(self, path: str) -> str:
        if self._engine is None:
            self._engine = os.path.basename(os.path.dirname(path))
        return self._engine

    def _schema(self, path: str, version: str) -> Dict:
        schema_path = os.path.join(os.path.dirname(path), "schema_{version}.yaml".format(version=version))
        if not os.path.exists(schema_path):
            raise Exception("Plugin schema path {schema_path} not found".format(schema_path=schema_path))
        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)
        return schema
