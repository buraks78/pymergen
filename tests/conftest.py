import pytest
import os
from unittest.mock import MagicMock
from pymergen.entity.plan import EntityPlan
from pymergen.entity.suite import EntitySuite
from pymergen.entity.case import EntityCase
from pymergen.entity.command import EntityCommand

# Add pytest configuration and shared fixtures here

@pytest.fixture
def plan():
    """Create a basic EntityPlan instance"""
    return EntityPlan()

@pytest.fixture
def suite():
    """Create a basic EntitySuite instance"""
    return EntitySuite()

@pytest.fixture
def case():
    """Create a basic EntityCase instance"""
    return EntityCase()

@pytest.fixture
def command():
    """Create a basic EntityCommand instance"""
    return EntityCommand()

@pytest.fixture
def fixtures_path():
    """Return the absolute path to the test fixtures directory"""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "fixtures")
