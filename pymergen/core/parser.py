import os
import re
import glob
import importlib
import cerberus
import pprint
import yaml
from typing import Any, List, Dict
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand
from pymergen.core.context import Context
from pymergen.controller.factory import ControllerFactory
from pymergen.controller.group import ControllerGroup
from pymergen.collector.collector import Collector


class Parser:

    def __init__(self, context: Context):
        self._context = context
        self._plans = list()
        self._validator = None
        self._init_validator()

    @property
    def context(self) -> Context:
        return self._context

    def load(self):
        path = self.context.plan_path
        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "*.yaml"))
            if len(files) == 0:
                raise Exception("No YAML files are found in {}".format(path))
            for file in files:
                data = self._load_yaml(file)
                self._validate_document(data, file)
                self._plans.extend(data["plans"])
        if os.path.isfile(path):
            if not path.endswith(".yaml"):
                raise Exception("Only YAML files are supported")
            data = self._load_yaml(path)
            self._validate_document(data, path)
            self._plans.extend(data["plans"])

    def parse(self) -> List[EntityPlan]:
        plans = [self._parse_plan(plan) for plan in self._plans]
        if self.context.filter_plan is not None:
            self.context.logger.debug("Plan filter is {f}".format(f=self.context.filter_plan))
            plans = [plan for plan in plans if re.search(self.context.filter_plan, plan.name, flags=re.IGNORECASE)]
        return plans

    def _parse_plan(self, data: Dict) -> EntityPlan:
        plan = EntityPlan()
        plan.name = data["name"]
        config = data.get("config", {})
        plan.config.replication = config.get("replication", 1)
        plan.config.params = config.get("params", dict())
        plan.config.iters = config.get("iters", dict())
        plan.pre = self._parse_commands(data.get("pre", []))
        plan.post = self._parse_commands(data.get("post", []))
        plan.cgroups = self._parse_cgroups(data.get("cgroups", []))
        plan.collectors = self._parse_collectors(data.get("collectors", []))
        for s in data["suites"]:
            suite = self._parse_suite(s)
            if self.context.filter_suite is not None:
                self.context.logger.debug("Suite filter is {f}".format(f=self.context.filter_suite))
                if re.search(self.context.filter_suite, suite.name, flags=re.IGNORECASE):
                    plan.add_suite(suite)
            else:
                plan.add_suite(suite)
        return plan

    def _parse_suite(self, data: Dict) -> EntitySuite:
        suite = EntitySuite()
        suite.name = data["name"]
        config = data.get("config", {})
        suite.config.replication = config.get("replication", 1)
        suite.config.concurrency = config.get("concurrency", False)
        suite.config.params = config.get("params", dict())
        suite.config.iters = config.get("iters", dict())
        suite.pre = self._parse_commands(data.get("pre", []))
        suite.post = self._parse_commands(data.get("post", []))
        for c in data["cases"]:
            case = self._parse_case(c)
            if self.context.filter_case is not None:
                self.context.logger.debug("Case filter is {f}".format(f=self.context.filter_case))
                if re.search(self.context.filter_case, case.name, flags=re.IGNORECASE):
                    suite.add_case(case)
            else:
                suite.add_case(case)
        return suite

    def _parse_case(self, data: Dict) -> EntityCase:
        case = EntityCase()
        case.name = data["name"]
        config = data.get("config", {})
        case.config.replication = config.get("replication", 1)
        case.config.parallelism = config.get("parallelism", 1)
        case.config.params = config.get("params", dict())
        case.config.iters = config.get("iters", dict())
        case.pre = self._parse_commands(data.get("pre", []))
        case.post = self._parse_commands(data.get("post", []))
        case.commands = self._parse_commands(data.get("commands", []))
        return case

    def _parse_commands(self, data: List[Dict]) -> List[EntityCommand]:
        commands = list()
        for item in data:
            command = EntityCommand()
            command.name = item.get("name")
            command.cmd = item.get("cmd")
            command.become_cmd = item.get("become_cmd", None)
            command.raise_error = item.get("raise_error", True)
            command.run_time = item.get("run_time", 0)
            command.shell = item.get("shell", False)
            command.shell_executable = item.get("shell_executable", None)
            command.timeout = item.get("timeout", None)
            command.pipe_stdout = item.get("pipe_stdout", None)
            command.pipe_stderr = item.get("pipe_stderr", None)
            command.debug_stdout = item.get("debug_stdout", False)
            command.debug_stderr = item.get("debug_stderr", False)
            command.cgroups = item.get("cgroups", list())
            commands.append(command)
        return commands

    def _parse_cgroups(self, data: List) -> List[ControllerGroup]:
        cgroups = list()
        for item in data:
            cgroup = ControllerGroup(item.get("name"))
            cgroup.become_cmd = item.get("become_cmd", None)
            for c in item.get("controllers"):
                controller = ControllerFactory.instance(c.get("name"))
                for limit in c.get("limits", {}):
                    controller.add_limit(limit.get("key"), limit.get("value"))
                cgroup.add_controller(controller)
            cgroups.append(cgroup)
        return cgroups

    def _parse_collectors(self, data: List) -> List[Collector]:
        collectors = list()
        for item in data:
            collector_plugin = self.context.plugin_manager.get_collector_plugin(item.get("engine"))
            collector = collector_plugin.implementation(item)
            collector.context = self.context
            collectors.append(collector)
        return collectors

    def _init_validator(self) -> None:
        try:
            importlib.import_module("cerberus")
            self._validator = cerberus.Validator()
        except ModuleNotFoundError:
            self.context.logger.warning("Unable to load module cerberus")

    def _validate_document(self, document: Dict, path: str) -> None:
        if not self._validator:
            return
        version = document.get("version", "")
        if len(version) == 0:
            raise Exception("Document does not have a version defined")
        schema_file = "schema_{version}.yaml".format(version=version)
        schema_path = os.path.join(os.path.dirname(__file__), "../conf/schema", schema_file)
        if not os.path.exists(schema_path):
            raise Exception("Schema path {schema_path} does not exist".format(schema_path=schema_path))
        schema = self._load_yaml(schema_path)
        # Add collector schemas
        collector_schemas = schema.get('plans').get('schema').get('schema').get('collectors').get('schema').get('anyof')
        collector_schemas.clear()
        for plugin in self.context.plugin_manager.get_collector_plugins().values():
            plugin_schema = plugin.schema(version)
            collector_schemas.append(plugin_schema)
        # Validate document with schema
        self._validator.validate(document, schema)
        if self._validator.errors:
            pprint.pprint(document)
            pprint.pprint(self._validator.errors)
            raise Exception("Failed to validate document {path} due to: {error}".format(
                path=path,
                error=pprint.pformat(self._validator.errors)
            ))

    def _load_yaml(self, path: str) -> Dict:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        base_dir = os.path.dirname(path)
        data = self._load_includes(data, base_dir)
        return data

    def _load_includes(self, data: Any, base_dir: str) -> Any:
        if isinstance(data, str) and data.startswith("include:") and data.endswith(".yaml"):
            path = self._get_include_path(data, base_dir)
            return self._load_yaml(path)
        if isinstance(data, list):
            return [self._load_includes(item, base_dir) for item in data]
        if isinstance(data, dict):
            return {k: self._load_includes(v, base_dir) for k, v in data.items()}
        return data

    def _get_include_path(self, value: str, base_dir: str) -> str:
        path = re.sub(r"^include:", "", value)
        path = os.path.join(base_dir, path)
        if not os.path.exists(path):
            raise Exception("Failed to load include at {path}".format(path=path))
        return path
