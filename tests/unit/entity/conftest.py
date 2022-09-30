import pytest
from pymergen.entity.entity import Entity
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase


class EntityTest(Entity):
    """Test implementation of abstract Entity class"""

    def log_name(self) -> str:
        return f"Test[{self.name}]"


@pytest.fixture
def entity():
    return EntityTest()


@pytest.fixture
def plan():
    return EntityPlan()


@pytest.fixture
def suite():
    return EntitySuite()


@pytest.fixture
def case():
    return EntityCase()
