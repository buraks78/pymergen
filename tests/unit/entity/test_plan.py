import pytest
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand


class TestPlan:
    def test_plan_init(self, plan):
        """Test plan initialization"""
        assert plan._suites == []
        assert plan._cgroups == []


    def test_plan_suites(self, plan):
        """Test suites property"""
        assert plan.suites == []

        # Add a single suite
        suite1 = EntitySuite()
        suite1.name = "suite1"
        plan.add_suite(suite1)

        assert len(plan.suites) == 1
        assert plan.suites[0] == suite1
        assert suite1.parent == plan

        # Add multiple suites
        suite2 = EntitySuite()
        suite2.name = "suite2"
        suite3 = EntitySuite()
        suite3.name = "suite3"

        plan.suites = [suite2, suite3]

        assert len(plan.suites) == 2  # Previous suites are replaced
        assert plan.suites[0] == suite2
        assert plan.suites[1] == suite3
        assert suite2.parent == plan
        assert suite3.parent == plan


    def test_plan_cgroups(self, plan):
        """Test cgroups property"""
        assert plan.cgroups == []

        # Set cgroups
        test_cgroups = ["cgroup1", "cgroup2"]
        plan.cgroups = test_cgroups

        assert plan.cgroups == test_cgroups


    def test_plan_dir_name(self, plan):
        """Test dir_name method"""
        plan.name = "testplan"
        assert plan.dir_name() == "plan_testplan"


    def test_plan_log_name(self, plan):
        """Test log_name method"""
        plan.name = "testplan"

        assert plan.short_name() == "Plan[testplan]"
        assert plan.long_name() == "Plan[testplan]"


    def test_plan_inheritance(self):
        """Test inheritance from Entity class"""
        plan = EntityPlan()

        # Test inherited Entity properties
        assert hasattr(plan, "name")
        assert hasattr(plan, "config")
        assert hasattr(plan, "parent")
        assert hasattr(plan, "pre")
        assert hasattr(plan, "post")

        # Test setting name
        plan.name = "testplan"
        assert plan.name == "testplan"

        # Test pre/post functionality inherited from Entity
        pre_cmd = EntityCommand()
        pre_cmd.name = "precmd"
        pre_cmd.cmd = "echo pre"

        post_cmd = EntityCommand()
        post_cmd.name = "postcmd"
        post_cmd.cmd = "echo post"

        plan.add_pre(pre_cmd)
        plan.add_post(post_cmd)

        assert len(plan.pre) == 1
        assert len(plan.post) == 1
        assert plan.pre[0].name == "precmd"
        assert plan.post[0].name == "postcmd"
        assert plan.pre[0].parent == plan
        assert plan.post[0].parent == plan
        assert plan.pre[0].cmd == "echo pre"
        assert plan.post[0].cmd == "echo post"
