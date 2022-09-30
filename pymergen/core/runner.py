import os
import glob
import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from pymergen.entity.plan import EntityPlan
from pymergen.core.context import Context
from pymergen.core.executor import ControllingExecutor
from pymergen.core.executor import CollectingExecutor
from pymergen.core.executor import ReplicatingExecutor
from pymergen.core.executor import ConcurrentExecutor
from pymergen.core.executor import IteratingExecutor
from pymergen.core.executor import ParallelExecutor
from pymergen.core.executor import ProcessExecutor


class Runner:

    REPORT_FILES = "files"

    def __init__(self, context: Context):
        self._context = context

    @property
    def context(self) -> Context:
        return self._context

    # Executor hierarchy:
    # Plan {  Controller > Replication }
    #   Suite { Replication > [Collection] > Concurrency }
    #       Case { Replication > Iteration > [Collection] > Parallelism }
    #           Command
    def run(self, plans: List[EntityPlan]) -> None:
        for plan in plans:
            plan_re = ReplicatingExecutor(self.context, plan)
            plan_cne = ControllingExecutor(self.context, plan, plan.cgroups)
            plan_cne.add_child(plan_re)
            for suite in plan.suites:
                suite_cce = ConcurrentExecutor(self.context, suite)
                suite_re = ReplicatingExecutor(self.context, suite)
                plan_re.add_child(suite_re)
                # If a suite is configured with concurrency, then we need to encapsulate all child cases for collection.
                if suite.config.concurrency is True:
                    suite_cle = CollectingExecutor(self.context, suite, plan.collectors, plan.cgroups)
                    suite_cle.add_child(suite_cce)
                    suite_re.add_child(suite_cle)
                else:
                    suite_re.add_child(suite_cce)
                for case in suite.cases:
                    case_pe = ParallelExecutor(self.context, case)
                    for command in case.commands:
                        command_pe = ProcessExecutor(self.context, command)
                        case_pe.add_child(command_pe)
                    case_ie = IteratingExecutor(self.context, case)
                    # No suite concurrency configured means that we can run collectors for each child case.
                    if suite.config.concurrency is False:
                        case_cle = CollectingExecutor(self.context, case, plan.collectors, plan.cgroups)
                        case_cle.add_child(case_pe)
                        case_ie.add_child(case_cle)
                    else:
                        case_ie.add_child(case_pe)
                    case_re = ReplicatingExecutor(self.context, case)
                    case_re.add_child(case_ie)
                    suite_cce.add_child(case_re)
            plan_cne.execute(None)

    def report(self, options: Dict) -> None:
        report = dict()
        if options.get(self.REPORT_FILES):
            report[self.REPORT_FILES] = self._report_files()
        if len(report) > 0:
            print(json.dumps(report, indent=4))

    def _report_files(self) -> Dict:
        report = defaultdict(lambda: defaultdict(list))
        run_path = os.path.abspath(self.context.run_path)
        files = glob.glob("{run_path}/**/*".format(run_path=run_path), recursive=True)
        for file in files:
            if os.path.isfile(file):
                file_name = Path(file).stem
                file_name_parts = file_name.split(".")
                file_name_category = file_name_parts[0]
                report[file_name_category][file_name].append(file)
        return report
