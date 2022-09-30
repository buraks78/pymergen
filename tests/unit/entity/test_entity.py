import re
import pytest
from pymergen.entity.entity import Entity
from pymergen.entity.config import EntityConfig


class TestEntity:
    def test_entity_init(self, entity):
        """Test entity initialization"""
        assert entity._name is None
        assert isinstance(entity._config, EntityConfig)
        assert entity._parent is None
        assert entity._pre == []
        assert entity._post == []


    def test_entity_config(self, entity):
        """Test config property"""
        assert isinstance(entity.config, EntityConfig)

        # Verify config is mutable
        entity.config.replication = 3
        assert entity.config.replication == 3


    def test_entity_parent(self, entity):
        """Test parent property"""
        assert entity.parent is None

        # Set parent
        from tests.unit.entity.conftest import EntityTest
        parent = EntityTest()
        parent.name = "parent"
        entity.parent = parent

        assert entity.parent == parent
        assert entity.parent.name == "parent"


    def test_entity_name_valid(self, entity):
        """Test name property with valid values"""
        # Valid alphanumeric names
        valid_names = ["test", "Test123", "123", "T123456789", "test-dash", "test_underscore"]

        for name in valid_names:
            entity.name = name
            assert entity.name == name


    def test_entity_name_invalid(self, entity):
        """Test name property with invalid values"""
        # Invalid names with non-alphanumeric characters
        invalid_names = ["test space", "test@symbol"]

        for name in invalid_names:
            with pytest.raises(Exception) as exc_info:
                entity.name = name
            assert "can only contain" in str(exc_info.value)


    def test_entity_pre(self, entity):
        """Test pre property and methods"""
        # Initial state
        assert entity.pre == []

        # Add single pre item
        from tests.unit.entity.conftest import EntityTest
        pre1 = EntityTest()
        pre1.name = "pre1"
        entity.add_pre(pre1)

        assert len(entity.pre) == 1
        assert entity.pre[0] == pre1
        assert pre1.parent == entity

        # Add list of pre items
        from tests.unit.entity.conftest import EntityTest
        pre2 = EntityTest()
        pre2.name = "pre2"
        pre3 = EntityTest()
        pre3.name = "pre3"

        entity.pre = [pre2, pre3]

        assert len(entity.pre) == 2  # Previous items are replaced
        assert entity.pre[0] == pre2
        assert entity.pre[1] == pre3
        assert pre2.parent == entity
        assert pre3.parent == entity


    def test_entity_post(self, entity):
        """Test post property and methods"""
        # Initial state
        assert entity.post == []

        # Add single post item
        from tests.unit.entity.conftest import EntityTest
        post1 = EntityTest()
        post1.name = "post1"
        entity.add_post(post1)

        assert len(entity.post) == 1
        assert entity.post[0] == post1
        assert post1.parent == entity

        # Add list of post items
        from tests.unit.entity.conftest import EntityTest
        post2 = EntityTest()
        post2.name = "post2"
        post3 = EntityTest()
        post3.name = "post3"

        entity.post = [post2, post3]

        assert len(entity.post) == 2  # Previous items are replaced
        assert entity.post[0] == post2
        assert entity.post[1] == post3
        assert post2.parent == entity
        assert post3.parent == entity


    def test_entity_log_name(self, entity):
        """Test log_name method implementation"""
        entity.name = "testentity"
        assert entity.log_name() == "Test[testentity]"
