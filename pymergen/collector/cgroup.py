import os
import time
from io import TextIOBase
from typing import Self, List
from datetime import datetime
from pymergen.collector.thread import CollectorThread
from pymergen.core.executor import CollectingExecutorContext


class CollectorControllerGroupFile:

    _instances = dict()

    def __init__(self, path: str, mode: str):
        self._path = path
        self._mode = mode
        self._fh = None

    def __del__(self):
        if self._fh is not None and not self._fh.closed:
            self._fh.close()

    @property
    def fh(self) -> TextIOBase:
        if self._fh is None:
            self._fh = open(self._path, self._mode)
        return self._fh


class CollectorControllerGroupStatParser(CollectorControllerGroupFile):

    @staticmethod
    def instance(path: str, mode: str) -> Self:
        if path not in CollectorControllerGroupStatParser._instances:
            CollectorControllerGroupStatParser._instances[path] = CollectorControllerGroupStatParser(path, mode)
        return CollectorControllerGroupStatParser._instances[path]

    def parse_headers(self) -> List:
        headers = list()
        headers.append("timestamp")
        self.fh.seek(0)
        for i, input_line in enumerate(self.fh.readlines()):
            input_columns = input_line.split(" ")
            input_columns_len = len(input_columns)
            if input_columns_len < 2:
                raise Exception("Unable to parse headers from {path} in line: {input_line}".format(
                    path=self._path,
                    input_line=input_line)
                )
            # First input column is the field prefix, and the rest of the columns contain a part of the field
            # name to on the left side of the equal sign.
            #
            # For example:
            #
            # some avg10=0.00 avg60=0.00 avg300=0.00 total=219731
            # full avg10=0.00 avg60=0.00 avg300=0.00 total=146364
            if "=" in input_columns[1]:
                for j in range(1, input_columns_len):
                    column_parts = input_columns[j].split("=")
                    headers.append("{name}_{subname}".format(
                        name=input_columns[0].strip(),
                        subname=column_parts[0].strip())
                    )
            # Two column format where first column is the field name and the right column is the field value.
            #
            # For example:
            #
            # usage_usec 76128949
            # user_usec 45340836
            # system_usec 30788112
            else:
                headers.append(input_columns[0].strip())
        return headers

    def parse_values(self) -> List:
        values = list()
        values.append(datetime.now().isoformat())
        self.fh.seek(0)
        for i, input_line in enumerate(self.fh.readlines()):
            input_columns = input_line.split(" ")
            input_columns_len = len(input_columns)
            if input_columns_len < 2:
                raise Exception("Unable to parse headers from {path} in line: {input_line}".format(
                    path=self._path,
                    input_line=input_line)
                )
            if "=" in input_columns[1]:
                for j in range(1, input_columns_len):
                    column_parts = input_columns[j].split("=")
                    values.append(column_parts[1].strip())
            else:
                values.append(input_columns[1].strip())
        return values


class CollectorControllerGroupStatLogger(CollectorControllerGroupFile):

    def __init__(self, path: str, mode: str):
        super().__init__(path, mode)
        self._is_first_call = True

    @property
    def is_first_call(self) -> bool:
        result = self._is_first_call
        self._is_first_call = False
        return result

    @staticmethod
    def instance(path: str, mode: str) -> Self:
        if path not in CollectorControllerGroupStatLogger._instances:
            CollectorControllerGroupStatLogger._instances[path] = CollectorControllerGroupStatLogger(path, mode)
        return CollectorControllerGroupStatLogger._instances[path]

    def log_line(self, line: str) -> None:
        self.fh.write("{line}\n".format(line=line))
        self.fh.flush()


class CollectorControllerGroup(CollectorThread):

    def run(self, parent_context: CollectingExecutorContext) -> None:
        time.sleep(self.ramp)
        while self._join is False:
            for cgroup in parent_context.cgroups:
                for controller in cgroup.controllers:
                    for stat_file in controller.stat_files:
                        log_file_path = os.path.join(
                            self._executor.run_path(parent_context),
                            "collector.cgroup_{cgname}_{stat_file}.log".format(
                                cgname=cgroup.name,
                                stat_file=stat_file.replace(".", "_")
                            )
                        )
                        stat_logger = CollectorControllerGroupStatLogger.instance(log_file_path, 'a')
                        stat_file_path = os.path.join(cgroup.DIR_BASE, cgroup.name, stat_file)
                        stat_parser = CollectorControllerGroupStatParser.instance(stat_file_path, 'r')
                        if stat_logger.is_first_call:
                            stat_logger.log_line(" ".join(stat_parser.parse_headers()))
                        stat_logger.log_line(" ".join(stat_parser.parse_values()))
            time.sleep(self.interval)
