import csv
from configparser import ConfigParser

# config utils
def load_config(filename='config.ini'): 
    config=ConfigParser()
    config.read(filename)
    return config

def get_config(config, section=''):
    section_config = {}
    if (section != '' and config.has_section(section)):
        items = config.items(section)
        for item in items:
            section_config[item[0]] = item[1]
    return section_config

# config utils
def load_config_full(filename='config.ini'): 
    config=ConfigParser()
    config.read(filename)

    fullcfg = {}
    for section in config.sections():
        fullcfg[section]=get_config(config,section)
    return fullcfg
