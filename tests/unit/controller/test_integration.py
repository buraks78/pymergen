import pytest
from pymergen.controller.controller import Controller
from pymergen.controller.group import ControllerGroup
from pymergen.controller.factory import ControllerFactory


class TestControllerIntegration:
    def test_factory_and_group_integration(self):
        # Create controllers using factory
        cpu = ControllerFactory.instance(Controller.TYPE_CPU)
        memory = ControllerFactory.instance(Controller.TYPE_MEMORY)

        # Add limits to controllers
        cpu.add_limit("weight", 200)
        memory.add_limit("limit_in_bytes", "2G")

        # Create a group and add controllers
        group = ControllerGroup("test_integration")
        group.add_controller(cpu)
        group.add_controller(memory)

        # Verify controllers were added correctly
        assert len(group.controllers) == 2
        assert group.controllers[0].name == Controller.TYPE_CPU
        assert group.controllers[1].name == Controller.TYPE_MEMORY

        # Verify controller limits were preserved
        assert group.controllers[0].limits["weight"] == 200
        assert group.controllers[1].limits["limit_in_bytes"] == "2G"

        # Verify builders generate correct commands
        commands = group.builders()
        assert len(commands) == 3  # 1 for create, 2 for limits

        # Verify create command
        assert "cgcreate -g cpu,memory:test_integration" in commands[0].cmd

        # Verify limit commands
        limit_cmds = [cmd.cmd for cmd in commands[1:]]
        assert any("cgset -r cpu.weight=200 test_integration" in cmd for cmd in limit_cmds)
        assert any("cgset -r memory.limit_in_bytes=2G test_integration" in cmd for cmd in limit_cmds)

    def test_multiple_groups_with_same_controllers(self):
        # Create two controller groups that share controller types
        group1 = ControllerGroup("group1")
        group2 = ControllerGroup("group2")

        # Add CPU controllers to both groups with different limits
        cpu1 = ControllerFactory.instance(Controller.TYPE_CPU)
        cpu1.add_limit("weight", 100)
        group1.add_controller(cpu1)

        cpu2 = ControllerFactory.instance(Controller.TYPE_CPU)
        cpu2.add_limit("weight", 200)
        group2.add_controller(cpu2)

        # Verify each group has the correct controller with correct limits
        assert group1.controllers[0].limits["weight"] == 100
        assert group2.controllers[0].limits["weight"] == 200

        # Verify each group generates appropriate commands
        cmds1 = group1.builders()
        cmds2 = group2.builders()

        assert "cgcreate -g cpu:group1" in cmds1[0].cmd
        assert "cgset -r cpu.weight=100 group1" in cmds1[1].cmd

        assert "cgcreate -g cpu:group2" in cmds2[0].cmd
        assert "cgset -r cpu.weight=200 group2" in cmds2[1].cmd
