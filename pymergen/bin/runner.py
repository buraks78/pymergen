import argparse
from pymergen.core.parser import Parser
from pymergen.core.context import Context
from pymergen.core.runner import Runner

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--plan-path", action="store", type=str, required=True)
parser.add_argument("-w", "--work-path", action="store", type=str, required=True)
parser.add_argument("--plugin-path", action="store", type=str, required=False)
parser.add_argument("--filter-plan", action="store", type=str, required=False, metavar="REGEX", help="Filter plans by name")
parser.add_argument("--filter-suite", action="store", type=str, required=False, metavar="REGEX", help="Filter suites by name")
parser.add_argument("--filter-case", action="store", type=str, required=False, metavar="REGEX", help="Filter cases by name")
parser.add_argument("-l", "--log-level", action="store", type=str.upper, choices=["DEBUG", "INFO", "WARN", "ERROR"], default="INFO")
parser.add_argument("--report-files", action="store_true", default=False)
args = parser.parse_args()

context = Context(args)
context.validate()

parser = Parser(context)
parser.load()
plans = parser.parse()

runner = Runner(context)
runner.run(plans)
runner.report({
    runner.REPORT_FILES: args.report_files
})
