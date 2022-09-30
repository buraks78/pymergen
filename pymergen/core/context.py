import sys
import shutil
import os
import logging
from datetime import datetime
from pymergen.core.logger import Logger
from pymergen.plugin.manager import PluginManager


class Context:

    def __init__(self, args):
        self._plan_path = args.plan_path
        self._work_path = args.work_path
        self._plugin_path = args.plugin_path
        self._run_path = os.path.join(self._work_path, self._generate_run_path())
        self._log_level = args.log_level
        self._filter_plan = args.filter_plan
        self._filter_suite = args.filter_suite
        self._filter_case = args.filter_case
        self._prepare()
        self._init_logger()
        self._plugin_manager = None

    @property
    def plan_path(self) -> str:
        return self._plan_path

    @property
    def work_path(self) -> str:
        return self._work_path

    @property
    def plugin_path(self) -> str:
        return self._plugin_path

    @property
    def run_path(self) -> str:
        return self._run_path

    @property
    def log_level(self) -> str:
        return self._log_level

    @property
    def filter_plan(self) -> str:
        return self._filter_plan

    @property
    def filter_suite(self) -> str:
        return self._filter_suite

    @property
    def filter_case(self) -> str:
        return self._filter_case

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def plugin_manager(self) -> PluginManager:
        if self._plugin_manager is None:
            self._plugin_manager = PluginManager(self)
            self._plugin_manager.load()
        return self._plugin_manager

    def validate(self):
        if sys.platform != "linux":
            raise Exception("Linux support only")
        for binary in ["cgcreate", "cgset", "cgdelete", "cgexec", "perf"]:
            if shutil.which(binary) is None:
                raise Exception("Command {binary} not found".format(binary=binary))
        if not os.path.exists(self._plan_path):
            raise Exception("Plan path {path} does not exist".format(path=self._plan_path))

    def _prepare(self) -> None:
        if not os.path.isdir(self.work_path):
            os.mkdir(self.work_path)
        if not os.path.isdir(self.run_path):
            os.mkdir(self.run_path)

    def _init_logger(self):
        self._logger = Logger.logger(self)
        for handler in self._logger.handlers:
            if type(handler) is logging.StreamHandler:
                handler.setLevel(self._log_level)

    @staticmethod
    def _generate_run_path() -> str:
        return datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
