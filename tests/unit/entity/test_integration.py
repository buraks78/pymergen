import pytest
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand


class TestIntegration:
    def test_complete_entity_hierarchy(self):
        """Test creating a complete entity hierarchy"""
        # Create a complete hierarchy
        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.params = {"key_a": "value_a"}

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.params = {"key_b": "value_b"}

        case = EntityCase()
        case.name = "testcase"
        case.config.params = {"key_c": "value_c"}

        cmd = EntityCommand()
        cmd.name = "testcmd"
        cmd.cmd = "echo test"

        # Link them
        plan.add_suite(suite)
        suite.add_case(case)
        case.add_command(cmd)

        # Test relationships
        assert plan.suites[0] == suite
        assert suite.cases[0] == case
        assert case.commands[0] == cmd

        # Test parent-child relationships
        assert suite.parent == plan
        assert case.parent == suite
        assert cmd.parent == case

        # Test log names
        assert plan.long_name() == "Plan[testplan]"
        assert suite.long_name() == "Plan[testplan] > Suite[testsuite]"
        assert case.long_name() == "Plan[testplan] > Suite[testsuite] > Case[testcase]"
        assert cmd.long_name() == "Plan[testplan] > Suite[testsuite] > Case[testcase] > Command[testcmd]"


    def test_entity_config_inheritance(self):
        """Test config settings at different levels of the hierarchy"""
        # Create a complete hierarchy with different configs
        plan = EntityPlan()
        plan.name = "testplan"
        plan.config.replication = 3
        plan.config.params = {"key_a": "value_a", "shared": "plan_level"}

        suite = EntitySuite()
        suite.name = "testsuite"
        suite.config.concurrency = True
        suite.config.params = {"key_b": "value_b", "shared": "suite_level"}

        case = EntityCase()
        case.name = "testcase"
        case.config.parallelism = 4
        case.config.params = {"key_c": "value_c", "shared": "case_level"}

        # Link them
        plan.add_suite(suite)
        suite.add_case(case)

        # Test each entity has its own config
        assert plan.config.replication == 3
        assert suite.config.concurrency is True
        assert case.config.parallelism == 4

        # Test params at each level
        assert plan.config.params == {"key_a": "value_a", "shared": "plan_level"}
        assert suite.config.params == {"key_b": "value_b", "shared": "suite_level"}
        assert case.config.params == {"key_c": "value_c", "shared": "case_level"}


    def test_entity_hierarchy_with_pre_post(self):
        """Test pre and post actions at different levels"""
        # Create entities
        plan = EntityPlan()
        plan.name = "testplan"

        suite = EntitySuite()
        suite.name = "testsuite"

        case = EntityCase()
        case.name = "testcase"

        # Create pre/post commands
        plan_pre = EntityCommand()
        plan_pre.name = "planpre"
        plan_pre.cmd = "echo plan pre"

        plan_post = EntityCommand()
        plan_post.name = "planpost"
        plan_post.cmd = "echo plan post"

        suite_pre = EntityCommand()
        suite_pre.name = "suitepre"
        suite_pre.cmd = "echo suite pre"

        suite_post = EntityCommand()
        suite_post.name = "suitepost"
        suite_post.cmd = "echo suite post"

        case_pre = EntityCommand()
        case_pre.name = "casepre"
        case_pre.cmd = "echo case pre"

        case_post = EntityCommand()
        case_post.name = "casepost"
        case_post.cmd = "echo case post"

        # Add pre/post actions
        plan.add_pre(plan_pre)
        plan.add_post(plan_post)

        suite.add_pre(suite_pre)
        suite.add_post(suite_post)

        case.add_pre(case_pre)
        case.add_post(case_post)

        # Link hierarchy
        plan.add_suite(suite)
        suite.add_case(case)

        # Verify pre/post actions are connected properly
        assert plan.pre[0] == plan_pre
        assert plan.post[0] == plan_post
        assert plan_pre.parent == plan
        assert plan_post.parent == plan

        assert suite.pre[0] == suite_pre
        assert suite.post[0] == suite_post
        assert suite_pre.parent == suite
        assert suite_post.parent == suite

        assert case.pre[0] == case_pre
        assert case.post[0] == case_post
        assert case_pre.parent == case
        assert case_post.parent == case
