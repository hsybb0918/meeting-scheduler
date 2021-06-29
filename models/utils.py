# @File        : utils.py
# @Description :
# @Time        : 20 June, 2021
# @Author      : Cyan
import os
from configparser import ConfigParser


def get_config(section, key):
    config = ConfigParser()
    config.read(os.path.abspath(os.path.dirname(__file__)).split('models')[0] + 'config.ini')

    return config.get(section, key)


if __name__ == '__main__':
    print(get_config('default', 'slot_division'))
