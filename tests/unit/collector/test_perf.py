import pytest
from unittest.mock import MagicMock, patch
from pymergen.collector.perf import (
    CollectorPerf,
    CollectorPerfEvent,
    CollectorPerfStat,
    CollectorPerfProfile
)


class TestCollectorPerf:
    def test_init(self):
        """Test perf collector initialization"""
        collector = CollectorPerf()
        assert collector._name is None
        assert collector._context is None
        assert collector._executor is None
        assert collector._cmd is None
        assert collector._become_cmd is None
        assert collector._cmd_parts == []
        assert collector._custom == []

    def test_cmd_property(self):
        """Test cmd property with explicit value"""
        collector = CollectorPerf()
        collector._cmd = "explicit command"

        assert collector.cmd == "explicit command"

    def test_cmd_property_auto_prepare(self):
        """Test cmd property auto prepares command if not set explicitly"""
        class TestableCollectorPerf(CollectorPerf):
            def _prepare_cmd_parts(self):
                self._cmd_parts = ["part1", "part2", "part3"]

        collector = TestableCollectorPerf()
        assert collector.cmd == "part1 part2 part3"

    def test_prepare_cmd_parts_with_custom(self):
        """Test preparing command parts with custom options"""
        class TestableCollectorPerf(CollectorPerf):
            def _prepare_cmd_parts(self):
                super()._prepare_cmd_parts()
                self._cmd_parts.append("base_part")

        collector = TestableCollectorPerf()
        collector._custom = ["--custom-flag1", "--custom-flag2"]
        collector._prepare_cmd_parts()

        assert "--custom-flag1" in collector._cmd_parts
        assert "--custom-flag2" in collector._cmd_parts
        assert "base_part" in collector._cmd_parts

    def test_parse_custom(self):
        """Test parsing custom configuration"""
        collector = CollectorPerf()
        config = {
            "name": "perf_collector",
            "custom": ["--custom-option1", "--custom-option2"]
        }

        collector.parse(config)

        assert collector.name == "perf_collector"
        assert collector._custom == ["--custom-option1", "--custom-option2"]


class TestCollectorPerfEvent:
    def test_init(self):
        """Test perf event collector initialization"""
        collector = CollectorPerfEvent()
        assert collector._cmd_parts == []
        assert collector._cgroup_events == {}
        assert collector._system_events == []

    def test_cgroup_events_property(self):
        """Test cgroup_events property getter and setter"""
        collector = CollectorPerfEvent()
        events = {"cgroup1": ["event1", "event2"]}
        collector.cgroup_events = events
        assert collector.cgroup_events is events

    def test_add_cgroup_event(self):
        """Test adding cgroup event"""
        collector = CollectorPerfEvent()
        collector.add_cgroup_event("cgroup1", "event1")
        collector.add_cgroup_event("cgroup1", "event2")
        collector.add_cgroup_event("cgroup2", "event3")

        assert collector.cgroup_events == {
            "cgroup1": ["event1", "event2"],
            "cgroup2": ["event3"]
        }

    def test_system_events_property(self):
        """Test system_events property getter and setter"""
        collector = CollectorPerfEvent()
        events = ["event1", "event2"]
        collector.system_events = events
        assert collector.system_events is events

    def test_add_system_event(self):
        """Test adding system event"""
        collector = CollectorPerfEvent()
        collector.add_system_event("event1")
        collector.add_system_event("event2")

        assert collector.system_events == ["event1", "event2"]

    def test_parse(self):
        """Test parsing configuration"""
        collector = CollectorPerfEvent()
        config = {
            "name": "perf_events",
            "custom": ["--freq", "99"],
            "events": [
                {"cgroup": "cgroup1", "name": "cpu-cycles"},
                {"cgroup": "cgroup1", "name": "cache-misses"},
                {"cgroup": "cgroup2", "name": "instructions"},
                {"name": "page-faults"}  # System event (no cgroup)
            ]
        }

        collector.parse(config)

        assert collector.name == "perf_events"
        assert collector._custom == ["--freq", "99"]
        assert collector.cgroup_events == {
            "cgroup1": ["cpu-cycles", "cache-misses"],
            "cgroup2": ["instructions"]
        }
        assert collector.system_events == ["page-faults"]

    def test_prepare_cmd_parts(self):
        """Test preparing command parts"""
        collector = CollectorPerfEvent()
        collector.add_cgroup_event("cgroup1", "cpu-cycles")
        collector.add_cgroup_event("cgroup1", "cache-misses")
        collector.add_cgroup_event("cgroup2", "instructions")
        collector.add_system_event("page-faults")

        collector._prepare_cmd_parts()

        # Verify cgroup events are added correctly
        assert "-e '{cpu-cycles,cache-misses}'" in " ".join(collector._cmd_parts)
        assert "-G cgroup1" in " ".join(collector._cmd_parts)
        assert "-e '{instructions}'" in " ".join(collector._cmd_parts)
        assert "-G cgroup2" in " ".join(collector._cmd_parts)

        # Verify system events are added correctly
        assert "-a" in collector._cmd_parts
        assert "-e '{page-faults}'" in " ".join(collector._cmd_parts)

    def test_prepare_cmd_parts_with_custom(self):
        """Test preparing command parts with custom options"""
        collector = CollectorPerfEvent()
        collector._custom = ["--call-graph dwarf", "-F 99"]
        collector.add_system_event("cpu-cycles")

        collector._prepare_cmd_parts()

        cmd_str = " ".join(collector._cmd_parts)

        # Verify custom options are added after the regular options
        assert "-a" in collector._cmd_parts
        assert "-e '{cpu-cycles}'" in cmd_str
        assert "--call-graph dwarf" in collector._cmd_parts
        assert "-F 99" in collector._cmd_parts


class TestCollectorPerfStat:
    def test_init(self):
        """Test perf stat collector initialization"""
        collector = CollectorPerfStat()
        assert collector._cmd_parts == []
        assert collector._cgroup_events == {}
        assert collector._system_events == []

    def test_prepare_cmd_parts(self):
        """Test preparing command parts for perf stat"""
        collector = CollectorPerfStat()
        collector.add_cgroup_event("cgroup1", "cpu-cycles")
        collector.add_system_event("page-faults")

        collector._prepare_cmd_parts()

        cmd_str = " ".join(collector._cmd_parts)

        # Verify perf stat specific parts
        assert "perf stat record" in cmd_str
        assert "-o {m:context:run_path}/collector.perf_stat.data" in cmd_str

        # Verify events from parent class implementation
        assert "-e '{cpu-cycles}'" in cmd_str
        assert "-G cgroup1" in cmd_str
        assert "-a" in cmd_str
        assert "-e '{page-faults}'" in cmd_str


class TestCollectorPerfProfile:
    def test_init(self):
        """Test perf profile collector initialization"""
        collector = CollectorPerfProfile()
        assert collector._cmd_parts == []
        assert collector._cgroup_events == {}
        assert collector._system_events == []

    def test_prepare_cmd_parts(self):
        """Test preparing command parts for perf record"""
        collector = CollectorPerfProfile()
        collector.add_cgroup_event("cgroup1", "cpu-cycles")
        collector.add_system_event("page-faults")

        collector._prepare_cmd_parts()

        cmd_str = " ".join(collector._cmd_parts)

        # Verify perf record specific parts
        assert "perf record" in cmd_str
        assert "-o {m:context:run_path}/collector.perf_profile.data" in cmd_str

        # Verify events from parent class implementation
        assert "-e '{cpu-cycles}'" in cmd_str
        assert "-G cgroup1" in cmd_str
        assert "-a" in cmd_str
        assert "-e '{page-faults}'" in cmd_str
