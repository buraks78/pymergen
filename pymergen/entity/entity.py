import re
from typing import Self, List
from pymergen.entity.config import EntityConfig


class Entity:

    def __init__(self):
        self._name = None
        self._config = EntityConfig()
        self._parent = None
        self._pre = list()
        self._post = list()

    @property
    def config(self) -> EntityConfig:
        return self._config

    @property
    def parent(self) -> Self:
        return self._parent

    @parent.setter
    def parent(self, value: Self) -> None:
        self._parent = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if re.match('^[a-z0-9_\\-]+$', value, re.IGNORECASE) is None:
            raise Exception("Name {v} can only contain alpha-numeric characters, underscores, or dashes.".format(v=value))
        self._name = value

    @property
    def pre(self) -> List[Self]:
        return self._pre

    @pre.setter
    def pre(self, values: List[Self]) -> None:
        self._pre = list()
        for value in values:
            self.add_pre(value)

    def add_pre(self, value: Self) -> None:
        value.parent = self
        self._pre.append(value)

    @property
    def post(self) -> List[Self]:
        return self._post

    @post.setter
    def post(self, values: List[Self]) -> None:
        self._post = list()
        for value in values:
            self.add_post(value)

    def add_post(self, value: Self) -> None:
        value.parent = self
        self._post.append(value)

    def __str__(self) -> str:
        return self.short_name()

    def short_name(self) -> str:
        raise NotImplementedError()

    def long_name(self) -> str:
        raise NotImplementedError()
