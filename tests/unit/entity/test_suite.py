import pytest
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.plan import EntityPlan


class TestSuite:
    def test_suite_init(self, suite):
        """Test suite initialization"""
        assert suite._cases == []


    def test_suite_cases(self, suite):
        """Test cases property"""
        assert suite.cases == []

        # Add a single case
        case1 = EntityCase()
        case1.name = "case1"
        suite.add_case(case1)

        assert len(suite.cases) == 1
        assert suite.cases[0] == case1
        assert case1.parent == suite

        # Add multiple cases
        case2 = EntityCase()
        case2.name = "case2"
        case3 = EntityCase()
        case3.name = "case3"

        suite.cases = [case2, case3]

        assert len(suite.cases) == 2  # Previous cases are replaced
        assert suite.cases[0] == case2
        assert suite.cases[1] == case3
        assert case2.parent == suite
        assert case3.parent == suite


    def test_suite_dir_name(self, suite):
        """Test dir_name method"""
        suite.name = "testsuite"
        assert suite.dir_name() == "suite_testsuite"


    def test_suite_log_name(self):
        """Test log_name method"""
        # Create a hierarchy
        plan = EntityPlan()
        plan.name = "testplan"

        suite = EntitySuite()
        suite.name = "testsuite"

        # Link them
        plan.add_suite(suite)

        expected_short = "Suite[testsuite]"
        expected_long = "Plan[testplan] > Suite[testsuite]"

        assert suite.short_name() == expected_short
        assert suite.long_name() == expected_long


    def test_suite_inheritance(self):
        """Test inheritance from Entity class"""
        suite = EntitySuite()

        # Test inherited Entity properties
        assert hasattr(suite, "name")
        assert hasattr(suite, "config")
        assert hasattr(suite, "parent")
        assert hasattr(suite, "pre")
        assert hasattr(suite, "post")

        # Test setting name
        suite.name = "testsuite"
        assert suite.name == "testsuite"

        # Test pre/post functionality inherited from Entity
        pre_case = EntityCase()
        pre_case.name = "precase"

        post_case = EntityCase()
        post_case.name = "postcase"

        suite.add_pre(pre_case)
        suite.add_post(post_case)

        assert len(suite.pre) == 1
        assert len(suite.post) == 1
        assert suite.pre[0].name == "precase"
        assert suite.post[0].name == "postcase"
        assert suite.pre[0].parent == suite
        assert suite.post[0].parent == suite
