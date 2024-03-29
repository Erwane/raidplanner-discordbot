# -*- coding: utf-8 -*-

"""
Config class
"""

import argparse
import json
import os


class Config:
    __conf = None

    @staticmethod
    def read():
        if Config.__conf is None:
            root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

            with open(root_path + '/config/config.json', 'r') as f:
                Config.__conf = json.load(f)

            Config.__conf['root_path'] = root_path

            # Parse arguments
            parser = argparse.ArgumentParser()
            parser.add_argument('-v', '--verbose', type=bool, dest='verbose', help="Verbose mode")
            Config.__conf['args'] = parser.parse_args()

        return Config.__conf
