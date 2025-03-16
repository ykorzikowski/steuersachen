#!/usr/bin/python3

import string
import random
import os, logging, yaml
from yaml.loader import SafeLoader

CONFIG_PATH = os.getenv("CONFIG_PATH", "config")

class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)

class Helper:
    @staticmethod
    def generate_random_str(size=6, chars=string.ascii_uppercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def load_config_yml() -> dict:
        return Helper.load_yaml(f"{CONFIG_PATH}/config.yml")

    @staticmethod
    def load_yaml(yml_file_name: str) -> dict:
        Loader.add_constructor('!include', Loader.include)
        with open(yml_file_name) as f:
            yml = yaml.load(f, Loader=Loader)
        return yml
