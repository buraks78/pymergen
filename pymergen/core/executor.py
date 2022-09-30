import copy
import itertools
import os
import re
import threading
from typing import Any, List, Dict, Self
from pymergen.entity.entity import EntityConfig, Entity
from pymergen.entity.command import EntityCommand
from pymergen.entity.case import EntityCase
from pymergen.entity.suite import EntitySuite
from pymergen.entity.plan import EntityPlan
from pymergen.core.context import Context
from pymergen.core.process import Process
from pymergen.core.thread import Thread
from pymergen.core.stat import Stat
from pymergen.controller.group import ControllerGroup
from pymergen.collector.collector import Collector


class ExecutorContext:

    def __init__(self, parent: Self):
        self._parent = parent
        self._entity = None
        self._current = None
        self._prefix = None
        self._exclude_from_path = False

    @property
    def parent(self) -> Self:
        return self._parent

    @property
    def entity(self) -> Entity:
        return self._entity

    @entity.setter
    def entity(self, value: Entity):
        self._entity = value

    @property
    def current(self) -> int:
        return self._current

    @current.setter
    def current(self, value: int) -> None:
        self._current = value

    @property
    def exclude_from_path(self) -> bool:
        return self._exclude_from_path

    def id(self) -> str:
        return "{p}{c:03d}".format(p=self._prefix, c=self._current)


class ControllingExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "cne"
        self._exclude_from_path = True


class CollectingExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "cle"
        self._exclude_from_path = True
        self._cgroups = None

    @property
    def cgroups(self) -> List[ControllerGroup]:
        return self._cgroups

    @cgroups.setter
    def cgroups(self, values: List[ControllerGroup]) -> None:
        self._cgroups = values


class ReplicatingExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "r"


class ConcurrentExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "cce"
        self._exclude_from_path = True


class ParallelExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "p"


class IteratingExecutorContext(ExecutorContext):

    def __init__(self, parent: Self):
        super().__init__(parent)
        self._prefix = "i"
        self._iters = dict()

    @property
    def iters(self) -> Dict[str, str]:
        return self._iters

    @iters.setter
    def iters(self, value: Dict[str, str]) -> None:
        self._iters = value


class Executor:

    def __init__(self, context: Context, entity: Entity):
        self._context = context
        self._entity = entity
        self._children = list()

    @property
    def context(self) -> Context:
        return self._context

    @property
    def entity(self) -> Entity:
        return self._entity

    @property
    def children(self) -> List:
        return self._children

    @children.setter
    def children(self, values: List) -> None:
        self._children = values

    def add_child(self, value: Self) -> None:
        self._children.append(value)

    def execute(self, parent_context: ExecutorContext) -> None:
        self.execute_main(parent_context)

    def execute_pre(self, parent_context: ExecutorContext) -> None:
        for pre in self.entity.pre:
            pe = ProcessExecutor(self.context, pre)
            pe.execute(parent_context)

    def execute_main(self, parent_context: ExecutorContext) -> None:
        raise NotImplementedError()

    def execute_post(self, parent_context: ExecutorContext) -> None:
        for post in self.entity.post:
            pe = ProcessExecutor(self.context, post)
            pe.execute(parent_context)

    # Do NOT cache this logic. Parallel executor requires things to stay independent if we don't want to deal with cloned objects.
    def run_path(self, parent_context: ExecutorContext) -> str:
        names = dict()
        while parent_context is not None:
            if parent_context.exclude_from_path is True:
                parent_context = parent_context.parent
                continue
            entity = parent_context.entity.name
            if parent_context.entity.name not in names:
                names[entity] = list()
            names[entity].append(parent_context.id())
            parent_context = parent_context.parent
        dirs = list()
        for entity in reversed(names):
            dirs.append(entity)
            for name in reversed(names[entity]):
                dirs.append(name)
        run_path = os.path.join(self.context.run_path, *dirs)
        os.makedirs(run_path, exist_ok=True)
        return run_path

    def stat(self):
        return Stat()


class ControllingExecutor(Executor):

    def __init__(self, context: Context, entity: Entity, cgroups: List[ControllerGroup]):
        super().__init__(context, entity)
        self._cgroups = cgroups

    @property
    def cgroups(self) -> List[ControllerGroup]:
        return self._cgroups

    @cgroups.setter
    def cgroups(self, values: List[ControllerGroup]) -> None:
        self._cgroups = values

    def execute_main(self, parent_context: ExecutorContext) -> None:
        try:
            self._build(parent_context)
            for child in self.children:
                context = ControllingExecutorContext(parent_context)
                context.entity = self.entity
                child.execute(context)
        finally:
            self._destroy(parent_context)

    def _build(self, parent_context: ExecutorContext):
        for cgroup in self.cgroups:
            for command in cgroup.builders():
                context = ControllingExecutorContext(parent_context)
                context.entity = self.entity
                pe = ProcessExecutor(self.context, command)
                pe.execute(context)

    def _destroy(self, parent_context: ExecutorContext):
        for cgroup in self.cgroups:
            for command in cgroup.destroyers():
                context = ControllingExecutorContext(parent_context)
                context.entity = self.entity
                pe = ProcessExecutor(self.context, command)
                pe.execute(context)


class CollectingExecutor(Executor):

    def __init__(self, context: Context, entity: Entity, collectors: List[Collector], cgroups: List[ControllerGroup]):
        super().__init__(context, entity)
        self._collectors = collectors
        self._cgroups = cgroups
        self._executors = list()

    @property
    def collectors(self) -> List[Collector]:
        return self._collectors

    @collectors.setter
    def collectors(self, values: List[Collector]) -> None:
        self._collectors = values

    @property
    def cgroups(self) -> List[ControllerGroup]:
        return self._cgroups

    @cgroups.setter
    def cgroups(self, values: List[ControllerGroup]) -> None:
        self._cgroups = values

    @property
    def executors(self) -> List[Executor]:
        return self._executors

    def execute_main(self, parent_context: ExecutorContext) -> None:
        try:
            self._start_collectors(parent_context)
            for child in self.children:
                context = CollectingExecutorContext(parent_context)
                context.entity = self.entity
                child.execute(context)
        finally:
            self._stop_collectors()

    def _start_collectors(self, parent_context: ExecutorContext):
        for collector in self.collectors:
            context = CollectingExecutorContext(parent_context)
            context.entity = self.entity
            context.cgroups = self.cgroups
            collector.start(context)

    def _stop_collectors(self):
        for collector in self.collectors:
            collector.stop()


class ReplicatingExecutor(Executor):

    def execute_main(self, parent_context: ExecutorContext) -> None:
        for r in range(1, self.entity.config.replication + 1):
            self.context.logger.debug("{n} Execute[replication={r}]".format(n=self.entity, r=r))
            context = ReplicatingExecutorContext(parent_context)
            context.entity = self.entity
            context.current = r
            stat = self.stat()
            stat.start()
            try:
                self.execute_pre(context)
                for child in self.children:
                    child.execute(context)
            finally:
                # Try to perform post / clean up actions
                self.execute_post(context)
            stat.stop()
            stat.log(self.run_path(context))
            self.context.logger.debug("{n} Finish[replication={r} duration={d}]".format(n=self.entity, r=r, d=stat.timer.duration))

class ConcurrentExecutor(Executor):

    def execute_main(self, parent_context: ExecutorContext) -> None:
        if self.entity.config.concurrency:
            threads = list()
            self.context.logger.debug("{n} Execute[concurrency=true]".format(n=self.entity))
            c = 1
            for child in self.children:
                context = ConcurrentExecutorContext(parent_context)
                context.entity = self.entity
                context.current = c
                c += 1
                threads.append(threading.Thread(target=child.execute, args=[context]))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        else:
            self.context.logger.debug("{n} Execute[concurrency=false]".format(n=self.entity))
            for child in self.children:
                context = ConcurrentExecutorContext(parent_context)
                context.entity = self.entity
                context.current = 1
                child.execute(context)


class IteratingExecutor(Executor):

    def execute_main(self, parent_context: ExecutorContext) -> None:
        iter_vars = self._iter_vars()
        if len(iter_vars) > 0:
            # generate groups of iter values based on configuration
            iteration_type = self.entity.config.iteration
            if iteration_type == EntityConfig.ITERATION_TYPE_PRODUCT:
                iter_groups = itertools.product(*iter_vars.values())
            elif iteration_type == EntityConfig.ITERATION_TYPE_ZIP:
                iter_groups = zip(*iter_vars.values())
            else:
                raise Exception("Unknown iteration type {t}".format(t=iteration_type))
            # iterate with each group
            i = 1
            for iter_group in iter_groups:
                iters = dict(zip(iter_vars.keys(), iter_group))
                self.context.logger.debug("{n} Execute[iteration={i} iters={iters}]".format(n=self.entity, i=i, iters=iters))
                for child in self.children:
                    context = IteratingExecutorContext(parent_context)
                    context.entity = self.entity
                    context.current = i
                    context.iters = iters
                    child.execute(context)
                    i += 1
        else:
            self.context.logger.debug("{n} Execute[iteration=false]".format(n=self.entity))
            for child in self.children:
                context = IteratingExecutorContext(parent_context)
                context.entity = self.entity
                context.current = 1
                child.execute(context)

    def _iter_vars(self) -> Dict[str, List]:
        iter_vars = dict()
        e = self.entity
        while e is not None:
            if len(e.config.iters) > 0:
                for key, val in e.config.iters.items():
                    if key not in iter_vars:
                        iter_vars[key] = val
            e = e.parent
        return iter_vars


class ParallelExecutor(Executor):

    def execute_main(self, parent_context: ExecutorContext) -> None:
        parallelism = self.entity.config.parallelism
        if parallelism > 1:
            self.context.logger.debug("{n} Execute[parallelism={p}]".format(n=self.entity, p=parallelism))
            for child in self.children:
                threads = list()
                for p in range(1, parallelism + 1):
                    # If executor hierarchy is changed, deepcopy will be needed.
                    child_copy = copy.copy(child)
                    context = ParallelExecutorContext(parent_context)
                    context.entity = self.entity
                    context.current = p
                    threads.append(threading.Thread(target=child_copy.execute, args=[context]))
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
        else:
            self.context.logger.debug("{n} Execute[parallelism=false]".format(n=self.entity))
            for child in self.children:
                context = ParallelExecutorContext(parent_context)
                context.entity = self.entity
                context.current = 1
                child.execute(context)


class ProcessExecutor(Executor):

    def __init__(self, context: Context, entity: EntityCommand):
        super().__init__(context, entity)
        self._process = None

    def execute_main(self, parent_context: ExecutorContext) -> None:
        self._process = Process(self.context)
        self._process.command = self._command(parent_context)
        self._process.run()

    def _command(self, parent_context: ExecutorContext) -> EntityCommand:
        command = copy.copy(self.entity)
        command.cmd = self._prepare(command.cmd, parent_context)
        if command.become_cmd is not None:
            command.become_cmd = self._prepare_placeholders(command.become_cmd, parent_context)
        if command.pipe_stdout is not None:
            command.pipe_stdout = self._prepare_placeholders(command.pipe_stdout, parent_context)
        if command.pipe_stderr is not None:
            command.pipe_stderr = self._prepare_placeholders(command.pipe_stderr, parent_context)
        return command

    def _prepare(self, cmd, parent_context: ExecutorContext) -> str:
        cmd = self._prepare_placeholders(cmd, parent_context)
        cmd = self._sub_cgroup(cmd)
        cmd = self._sub_become(cmd)
        return cmd

    def _prepare_placeholders(self, cmd, parent_context: ExecutorContext) -> str:
        cmd = self._sub_context(cmd, parent_context)
        cmd = self._sub_entity(cmd)
        cmd = self._sub_params(cmd)
        cmd = self._sub_iters(cmd, parent_context)
        return cmd

    def _sub_context(self, cmd: str, parent_context: ExecutorContext) -> str:
        cmd = re.sub("{m:context:run_path}", self.run_path(parent_context), cmd)
        cmd = re.sub("{m:context:pid}", str(os.getpid()), cmd)
        cmd = re.sub("{m:context:ppid}", str(os.getppid()), cmd)
        cmd = re.sub("{m:context:pgid}", str(os.getpgid(os.getpid())), cmd)
        return cmd

    def _sub_entity(self, cmd: str) -> str:
        cmd = re.sub("{m:entity:command}", self.entity.name, cmd)
        # Support commands under pre and post sections
        if type(self.entity.parent) is EntityCase:
            cmd = re.sub("{m:entity:case}", self.entity.parent.name, cmd)
            cmd = re.sub("{m:entity:suite}", self.entity.parent.parent.name, cmd)
            cmd = re.sub("{m:entity:plan}", self.entity.parent.parent.parent.name, cmd)
        if type(self.entity.parent) is EntitySuite:
            cmd = re.sub("{m:entity:suite}", self.entity.parent.name, cmd)
            cmd = re.sub("{m:entity:plan}", self.entity.parent.parent.name, cmd)
        if type(self.entity.parent) is EntityPlan:
            cmd = re.sub("{m:entity:plan}", self.entity.parent.name, cmd)
        return cmd

    def _sub_params(self, cmd: str) -> str:
        e = self.entity
        while e is not None:
            for key, val in e.config.params.items():
                placeholder = "{{m:param:{key}}}".format(key=key)
                cmd = re.sub(re.escape(placeholder), val, cmd)
            e = e.parent
        return cmd

    def _sub_iters(self, cmd: str, parent_context: ExecutorContext) -> str:
        c = parent_context
        while c is not None:
            if hasattr(c, "iters") and c.iters is not None:
                for key, val in c.iters.items():
                    placeholder = "{{m:iter:{key}}}".format(key=key)
                    cmd = re.sub(re.escape(placeholder), val, cmd)
            c = c.parent
        return cmd

    def _sub_cgroup(self, cmd: str) -> str:
        cgroup_names = self.entity.cgroups
        if len(cgroup_names) > 0:
            parts = list()
            cgroups = self.entity.parent.parent.parent.cgroups
            for cgroup_name in cgroup_names:
                for cgroup in cgroups:
                    if cgroup.name == cgroup_name:
                        controllers = [c.name for c in cgroup.controllers]
                        parts.append("-g {controllers}:{cgroup_name}".format(controllers=",".join(controllers), cgroup_name=cgroup_name))
                        break
            if len(parts) == 0:
                raise Exception("No matching controller group found")
            cmd = "cgexec {parts} {cmd}".format(parts=" ".join(parts), cmd=cmd)
        return cmd

    def _sub_become(self, cmd: str) -> str:
        become_cmd = self.entity.become_cmd
        if become_cmd is not None:
            cmd = "{become_cmd} {cmd}".format(become_cmd=become_cmd, cmd=cmd)
        return cmd


class AsyncProcessExecutor(ProcessExecutor):

    def __init__(self, context: Context, entity: EntityCommand):
        super().__init__(context, entity)

    def execute_main(self, parent_context: ExecutorContext) -> None:
        self._process = Process(self.context)
        self._process.command = self._command(parent_context)
        self._process.start()

    def execute_stop(self) -> None:
        self._process.signal()
        self._process.wait()


class AsyncThreadExecutor(Executor):

    def __init__(self, context: Context, entity: Entity):
        super().__init__(context, entity)
        self._thread = None
        self._target = None

    @property
    def target(self) -> Any:
        return self._target

    @target.setter
    def target(self, value: Any) -> None:
        self._target = value

    def execute_main(self, parent_context: ExecutorContext):
        self._thread = Thread(self.context)
        self._thread.run(self._target, [parent_context])

    def execute_stop(self):
        self._target.join()
        self._thread.join()
