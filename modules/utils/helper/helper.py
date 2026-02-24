#!/usr/bin/python3

import os
import random
import string

import yaml

CONFIG_PATH = os.getenv("CONFIG_PATH", "config")


class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super().__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, "r", encoding="utf-8") as f:
            return yaml.load(f, Loader)


class Helper:
    @staticmethod
    def generate_random_str(size=6, chars=string.ascii_uppercase + string.digits) -> str:
        return "".join(random.choice(chars) for _ in range(size))

    @staticmethod
    def load_config_yml() -> dict:
        return Helper.load_yaml(f"{CONFIG_PATH}/config.yml")

    @staticmethod
    def load_yaml(yml_file_name: str) -> dict:
        Loader.add_constructor("!include", Loader.include)
        with open(yml_file_name, "r", encoding="utf-8") as f:
            yml = yaml.load(f, Loader=Loader)
        return yml
