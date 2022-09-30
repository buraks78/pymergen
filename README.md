# PyMergen

---

PyMergen is a configuration-driven test automation tool for Linux. It is intended to be a local command executor to automate repetitive and iterative testing actions on a Linux host to perform benchmarking and metric collection. The default collection logic is built around Linux Control Groups (cgroups) and Perf tools, and the functionality is extensible through a plugin mechanism.

Mergen is the Turkic deity of abundance and wisdom. PyMergen is the Pythonic deity of abundance and wisdom for Linux systems.

# Installation

```shell
python -m pip install pymergen
```

## Requirements

The following RPM packages are required when corresponding collector plugins are enabled.

| RPM (Fedora)    | Binaries                          |
|-----------------|-----------------------------------|
| libcgroup-tools | cgcreate, cgset, cgdelete, cgexec |
| perf            | perf                              |

# Usage

Basic command line:

```commandline
python -m pymergen.bin.runner -p examples/basic.yaml -w basic --report-files
python -m pymergen.bin.runner -p examples/test.yaml -w test --report-files
```

# Concepts

## Testing

PyMergen is built around a conventional testing design. This essentially boils down to the concept of testing **entities** and the hierarchical relationship among them. 

There are four main entities: **plans**, **suites**, **cases**, and **commands**. At the top of the configuration hierarchy, there are plans. Each plan consists of multiple suites. Each suite, in turn, is composed of multiple cases. Finally, commands assigned to each case constitute the bottom layer.

```text
Plan
└── Suite
    └── Case
        └── Command
```

Each entity supports **pre** and **post** sections to execute setup and teardown commands for the respective entity. See `examples/test.yaml` file for details.

## Benchmarking

### Replication

Replication involves running identical test scenarios repetitively to validate result consistency and identify anomalies. Replication configuration is supported by plan, suite, and case entities. It is defined using the `replication` parameter. This setting expects an integer value and defaults to `1` (i.e., no replication).

### Concurrency

Concurrent execution simulates distinct scenarios accessing the system under test at the same time. It is intended to test system behavior under simultaneous but different load conditions to identify any contention points. Concurrency configuration is supported by suite entities only. It is defined by the `concurrency` parameter which expects a boolean value. When set to `true`, all cases defined under a suite are executed concurrently. Defaults to `false`.

### Parallelism

Parallel execution mode is intended to simulate identical scenarios running at the same time. Parallelism configuration is supported by case entities only. It is defined using the `parallelism` parameter. This setting expects an integer value and defaults to `1`.

### Iteration

Iteration involves repeating test commands with varying parameters to evaluate performance behavior. It is intended to reveal how performance scales with changing inputs or configurations. There is no specific configuration parameter for this functionality. It instead consists of a set of parameters that are defined at plan, suite, or case levels, and the iteration behavior is triggered by the use of corresponding placeholders embedded inside a command entity.

#### Iteration Placeholders

The placeholder format is `{m:iter:<name>}`. Each placeholder corresponds to a parameter defined in the entity configuration. Iteration parameters are expected to be lists. Depending on the placeholders used in the command, corresponding parameters in the entity hierarchy up to the top plan level are gathered and combined into a multi-level list through a selected iteration method. Note that lower level parameters have a higher priority than upper level parameters to support overriding. The final list items are then used as inputs to customize each command for iteration. See `examples/basic.yaml` file for an example implementation.

#### Iteration Method

There are two different methods to combine parameters for iterative execution. The first is the `product` method which can be represented in the command line as follows:

```python
import itertools
var1 = ["A", "B"]
var2 = ["C", "D"]
list(itertools.product(var1, var2)) # [('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D')]
```
A command entity containing placeholders for both `{m:iter:var1}` and `{m:iter:var2}` would be executed a total of four times in this method.

The second iteration method is the `zip` method:

```python
var1 = ["A", "B"]
var2 = ["C", "D"]
list(zip(var1, var2)) # [('A', 'C'), ('B', 'D')]
```

In this latter case, a command entity containing both `{m:iter:var1}` and `{m:iter:var2}` would be executed twice, first time with A and C, and the second time with B and D.

The iteration method is defined by the `iterate` configuration parameter. Accepted values are `product` and `zip`. The default method is `product`.

## Collection

The collection framework is a mechanism for gathering, organizing, and reporting test data. Collectors are tasked with logging structured resource usage statistics as output.

There are different collector types, each focusing on different execution models. *Process Collectors* manage external processes for data collection. There are also *Thread Collectors* that run native threads with configurable intervals. 

Collector execution can happen at two different levels:
* Suite-Level Wrapping
  * When `concurrency=true` for a suite, collector logic wraps around all cases in the suite, allowing collectors to monitor the entire suite execution as a unit.
* Case-Level Wrapping
  * When `concurrency=false` (default setting), all commands under a case are wrapped individually after iteration parameters are applied. Note that wrapping at this level also includes the parallel execution context. See the *Execution* section for more information.

Collectors are configured at the plan level. See `examples/test.yaml` file for details.

### Controller Groups

The standard collection mechanism is built around Linux Control Groups (cgroups) and integrates with the execution hierarchy through the `ControllingExecutor`.

The configuration follows the same hierarchical structure as Linux cgroups: *Controller Groups* are top-level entities that manage collections of related controllers. *Controllers* are individual resource controllers that manage specific system resources under each group. Finally, *controller limits* are configuration parameters that define resource constraints for each controller.

### Collector Plugins

Collector plugins are configured at the plan level and integrated into the execution hierarchy, providing performance monitoring capabilities.

#### Cgroup Collector

The Cgroup Collector plugin monitors Linux Control Groups (cgroups) resources at configurable intervals by running native threads. It logs structured resource usage statistics for cgroups associated with each command entity.

#### Perf Stat Collector

The Perf Stat Collector plugin integrates with `perf stat` utility to collect system-wide and/or cgroup-specific performance statistics during test execution. This collector is a simple wrapper around `perf stat`.

#### Perf Profile Collector

The Perf Profile Collector plugin leverages `perf record` functionality to generate detailed performance profiles of applications under test. This collector is intended to be a simple wrapper around `perf record`.

#### Command Collector

The Command Collector plugin provides a flexible interface to execute custom commands beyond the standard set of collectors implemented. This collector extends the default performance collection capabilities by allowing any arbitrary command to be executed as a collection mechanism.

## Execution

The relationship between entities forms the basis of the execution hierarchy. This hierarchy changes a bit based on the concurrency setting for a suite, as explained under the *Collection* section.
```text
Plan:
  ControllingExecutor
    ReplicatingExecutor
      Suite:
        ReplicatingExecutor 
          CollectingExecutor [if concurrency=true]
            ConcurrentExecutor
              Case:
                ReplicatingExecutor
                  IteratingExecutor
                    CollectingExecutor [if concurrency=false]
                      ParallelExecutor
                        Command:
                          ProcessExecutor
```

### Command Configuration

Command entities constitute the heart of the execution process. The following attributes are available for command configuration: 

* `name`
  * Unique identifier for the command entity for logging purposes.
* `cmd`
  * Main command to be executed.
* `become_cmd`
  * Command to execute to elevate privileges. 
  * This is basically a prefix for the `cmd` string. For example: `sudo -i -u test`
* `raise_error`
  * Boolean flag to throw exceptions when Python Popen implementation raises errors. Default is `true`. 
  * Note that commands returning non-zero return codes do not fall under this failure definition.
* `run_time`
  * Number of seconds to allow the command to run. The process is then sent a SIGINT signal to stop it. Default is `0` which disables this behavior.
* `timeout`
  * Number of seconds to wait for the command to return before throwing a timeout exception. 
  * `raise_error` configuration parameter controls whether the timeout exception is propagated up.
* `shell`
  * Boolean flag to turn on shell support. Default is `false`.
  * If `cmd` requires shell functionality to be enabled (such as parameter expansion, command substitution, output redirection, etc.), this configuration option must be set to `true`.
* `shell_executable`
  * Option to override default shell executable.
* `debug_stdout`
  * Boolean flag to turn on command stdout logging to runner (debug) log.
* `debug_stderr`
  * Boolean flag to turn on command stderr logging to runner (debug) log.
* `pipe_stdout`
  * Configuration option to direct the command stdout to a specific path.
  * Disables `debug_stdout` behavior.
* `pipe_stderr`
  * Configuration option to direct the command stderr to a specific path.
  * Disables `debug_stderr` behavior.
* `cgroups`
  * List of cgroup names to run the command under. 
  * Each cgroup name must correspond to an existing cgroup configuration defined under the respective plan.

### Command Customization

A short list of placeholders to help with customization is available:

* Context Placeholders
  * `{m:context:run_path}`: Current execution directory for command entity.
  * `{m:context:pid}`: Main PID for the PyMergen process
  * `{m:context:ppid}`: Parent PID for the PyMergen process
  * `{m:context:pgid}`: Group PID for the PyMergen process
* Entity Placeholders
  * `{m:entity:plan}`: Refers to plan name
  * `{m:entity:suite}`: Refers to suite name
  * `{m:entity:case}`: Refers to case name
  * `{m:entity:command}`: Refers to command name
* Parameter Placeholders
  * `{m:param:<name>}`: Points to an entry defined in the list of parameters for entities.
* Iteration Placeholders
  * `{m:iter:<name>}`: Enables iteration functionality. See *Iteration* section for more information.

## Output 

### Directory Structure

Test results are organized hierarchically based on test execution:

```text
work_path/YYYYMMDD_HHMMSS/   # Timestamped run directory
├── plan1/                   
│   ├── r001/                # Plan replication instance 1
│   │   ├── suite1/          
│   │   │   ├── r001/        # Suite replication instance 1
│   │   │   │   ├── case1/   
│   │   │   │   │   ├── r001/      # Case replication instance 1
│   │   │   │   │   │   ├── i001/  # Iteration instance 1
│   │   │   │   │   │   │   ├── p001/  # Parallel instance 1
│   │   │   │   │   │   │   │   └── [command outputs, logs, etc.]
│   │   │   │   │   │   │   ├── p002/  # Parallel instance 2
│   │   │   │   │   │   │   │   └── [command outputs, logs, etc.]
│   │   │   │   │   │   │   └── p003/  # Parallel instance 3
│   │   │   │   │   │   │       └── [command outputs, logs, etc.]
│   │   │   │   │   │   └── i002/  # Iteration instance 2
│   │   │   │   │   │       └── [parallel instances for commands]
│   │   │   │   │   └── r002/      # Case replication instance 2
│   │   │   │   │       └── [iteration instances]
│   │   │   │   ├── case2/   
│   │   │   │   │   └── [replication, iteration, parallel instances]
│   │   │   │   └── case3/   
│   │   │   │       └── [replication, iteration, parallel instances]
│   │   │   └── r002/        # Suite replication instance 2
│   │   │       └── [case directories]
│   │   └── suite2/
│   │       └── [replication, case directories]
│   └── r002/                # Plan replication instance 2
│       └── [suite directories]
└── plan2/
    └── [replication, suite directories]
```

Each directory level in the path corresponds to a specific entity and its assigned execution contexts:
* Timestamp Directory (`YYYYMMDD_HHMMSS`)
  * Root directory for each test run
* Entity Directories
  * Named according to the entity name (e.g. `case1`)
* Execution Context Directories
  * Replication execution instance (`r###`)
  * Iteration execution instance (`i###`)
  * Parallel execution instance (`p###`)
  
Some execution contexts are excluded and do not appear in the output directory structure. This is to keep the directory structure focused on the actual test hierarchy rather than on implementation details.

* Controlling Executor Context (`cne###`)
* Collecting Executor Context (`cle###`)
* Concurrency Executor Context (`cce###`)

This hierarchical approach makes it easier to locate and analyze test results across different execution contexts while preventing output file conflicts.

### File Grouping

Generated files are organized based on filename patterns. This method recursively scans the test run directory for all files, then parses each filename by splitting it at period delimiters. The components of the file name are then used to create a nested dictionary structure. Files are first categorized by their prefix component, then grouped by their complete stem name, with each group containing a list of absolute file paths.

## TODO

* Aggregator logic and plugins to parse and report collected data
