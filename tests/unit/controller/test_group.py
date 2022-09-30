import pytest
from pymergen.controller.controller import Controller, ControllerCpu, ControllerMemory
from pymergen.controller.group import ControllerGroup
from pymergen.entity.command import EntityCommand


class TestControllerGroup:
    def test_init(self):
        group = ControllerGroup("test_group")
        assert group.name == "test_group"
        assert group.become_cmd is None
        assert group.controllers == []

    def test_become_cmd_property(self):
        group = ControllerGroup("test_group")
        assert group.become_cmd is None

        group.become_cmd = "sudo"
        assert group.become_cmd == "sudo"

    def test_add_controller(self):
        group = ControllerGroup("test_group")
        cpu = ControllerCpu()
        memory = ControllerMemory()

        group.add_controller(cpu)
        assert len(group.controllers) == 1
        assert group.controllers[0] == cpu

        group.add_controller(memory)
        assert len(group.controllers) == 2
        assert group.controllers[1] == memory

    def test_controllers_setter(self):
        group = ControllerGroup("test_group")
        controllers = [ControllerCpu(), ControllerMemory()]
        group.controllers = controllers
        assert group.controllers == controllers

    def test_controller_names(self):
        group = ControllerGroup("test_group")
        cpu = ControllerCpu()
        memory = ControllerMemory()
        group.add_controller(cpu)
        group.add_controller(memory)

        names = group._controller_names()
        assert "cpu" in names
        assert "memory" in names
        assert len(names) == 2

    def test_builders(self):
        group = ControllerGroup("test_group")
        cpu = ControllerCpu()
        cpu.add_limit("weight", 100)
        group.add_controller(cpu)

        commands = group.builders()
        assert len(commands) == 2
        assert isinstance(commands[0], EntityCommand)
        assert "cgcreate_test_group" == commands[0].name
        assert "cgcreate -g cpu:test_group" in commands[0].cmd
        assert "cgset -r cpu.weight=100 test_group" in commands[1].cmd
        assert commands[0].become_cmd is None

    def test_builders_with_become_cmd(self):
        group = ControllerGroup("test_group")
        group.become_cmd = "sudo"
        cpu = ControllerCpu()
        cpu.add_limit("weight", 100)
        group.add_controller(cpu)

        commands = group.builders()
        assert len(commands) == 2
        assert isinstance(commands[0], EntityCommand)
        assert "cgcreate -g cpu:test_group" in commands[0].cmd
        assert "cgset -r cpu.weight=100 test_group" in commands[1].cmd
        assert commands[0].become_cmd == "sudo"
        assert commands[1].become_cmd == "sudo"

    def test_destroyers(self):
        group = ControllerGroup("test_group")
        cpu = ControllerCpu()
        memory = ControllerMemory()
        group.add_controller(cpu)
        group.add_controller(memory)

        commands = group.destroyers()
        assert len(commands) == 1
        assert isinstance(commands[0], EntityCommand)
        assert "cgdelete_test_group" == commands[0].name
        assert "cgdelete -g cpu,memory:test_group" in commands[0].cmd
        assert commands[0].become_cmd is None

    def test_destroyers_with_become_cmd(self):
        group = ControllerGroup("test_group")
        group.become_cmd = "sudo"
        cpu = ControllerCpu()
        memory = ControllerMemory()
        group.add_controller(cpu)
        group.add_controller(memory)

        commands = group.destroyers()
        assert len(commands) == 1
        assert isinstance(commands[0], EntityCommand)
        assert "cgdelete -g cpu,memory:test_group" in commands[0].cmd
        assert commands[0].become_cmd == "sudo"

    def test_empty_controller_group(self):
        group = ControllerGroup("empty_group")
        assert group._controller_names() == []

        builders = group.builders()
        assert len(builders) == 1
        assert "cgcreate -g :empty_group" in builders[0].cmd

        destroyers = group.destroyers()
        assert len(destroyers) == 1
        assert "cgdelete -g :empty_group" in destroyers[0].cmd
