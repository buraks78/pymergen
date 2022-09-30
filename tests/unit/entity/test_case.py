import pytest
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand
from pymergen.entity.suite import EntitySuite
from pymergen.entity.plan import EntityPlan


class TestCase:
    def test_case_init(self, case):
        """Test case initialization"""
        assert case._commands == []


    def test_case_commands(self, case):
        """Test commands property"""
        assert case.commands == []

        # Add a single command
        cmd1 = EntityCommand()
        cmd1.name = "cmd1"
        case.add_command(cmd1)

        assert len(case.commands) == 1
        assert case.commands[0] == cmd1
        assert cmd1.parent == case

        # Add multiple commands
        cmd2 = EntityCommand()
        cmd2.name = "cmd2"
        cmd3 = EntityCommand()
        cmd3.name = "cmd3"

        case.commands = [cmd2, cmd3]

        assert len(case.commands) == 2  # Previous commands are replaced
        assert case.commands[0] == cmd2
        assert case.commands[1] == cmd3
        assert cmd2.parent == case
        assert cmd3.parent == case


    def test_case_dir_name(self, case):
        """Test dir_name method"""
        case.name = "testcase"
        assert case.dir_name() == "case_testcase"


    def test_case_log_name(self):
        """Test log_name method"""
        # Create a hierarchy
        plan = EntityPlan()
        plan.name = "testplan"

        suite = EntitySuite()
        suite.name = "testsuite"

        case = EntityCase()
        case.name = "testcase"

        # Link them
        plan.add_suite(suite)
        suite.add_case(case)

        expected_short = "Case[testcase]"
        expected_long = "Plan[testplan] > Suite[testsuite] > Case[testcase]"

        assert case.short_name() == expected_short
        assert case.long_name() == expected_long


    def test_case_inheritance(self):
        """Test inheritance from Entity class"""
        case = EntityCase()

        # Test inherited Entity properties
        assert hasattr(case, "name")
        assert hasattr(case, "config")
        assert hasattr(case, "parent")
        assert hasattr(case, "pre")
        assert hasattr(case, "post")

        # Test pre/post functionality inherited from Entity
        cmd_pre = EntityCommand()
        cmd_pre.name = "precmd"
        cmd_pre.cmd = "echo pre"

        cmd_post = EntityCommand()
        cmd_post.name = "postcmd"
        cmd_post.cmd = "echo post"

        case.add_pre(cmd_pre)
        case.add_post(cmd_post)

        assert len(case.pre) == 1
        assert len(case.post) == 1
        assert case.pre[0].name == "precmd"
        assert case.post[0].name == "postcmd"
        assert case.pre[0].parent == case
        assert case.post[0].parent == case
