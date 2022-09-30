from pymergen.entity.config import EntityConfig


class TestConfig:
    def test_config_default_values(self):
        config = EntityConfig()
        assert config.replication == 1
        assert config.concurrency is False
        assert config.parallelism == 1
        assert config.iteration == EntityConfig.ITERATION_TYPE_PRODUCT
        assert config.params == {}
        assert config.iters == {}


    def test_config_replication(self):
        config = EntityConfig()

        # Test setter
        config.replication = 5
        assert config.replication == 5


    def test_config_concurrency(self):
        config = EntityConfig()

        # Test setter
        config.concurrency = True
        assert config.concurrency is True


    def test_config_parallelism(self):
        config = EntityConfig()

        # Test setter
        config.parallelism = 4
        assert config.parallelism == 4


    def test_config_iteration(self):
        config = EntityConfig()

        # Test valid values
        config.iteration = EntityConfig.ITERATION_TYPE_PRODUCT
        assert config.iteration == EntityConfig.ITERATION_TYPE_PRODUCT

        config.iteration = EntityConfig.ITERATION_TYPE_ZIP
        assert config.iteration == EntityConfig.ITERATION_TYPE_ZIP



    def test_config_params(self):
        config = EntityConfig()

        # Test empty dict
        config.params = {}
        assert config.params == {}

        # Test with values
        test_params = {"key1": "value1", "key2": "value2"}
        config.params = test_params
        assert config.params == test_params


    def test_config_iters(self):
        config = EntityConfig()

        # Test empty dict
        config.iters = {}
        assert config.iters == {}

        # Test with values
        test_iters = {"iter1": ["val1", "val2"], "iter2": ["val3", "val4"]}
        config.iters = test_iters
        assert config.iters == test_iters
