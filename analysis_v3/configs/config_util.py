import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v3.configs import flat_config_elastic, flat_config_plastic, curved_config_elastic, curved_config_plastic


def get_config(shape, plastic):
    if shape == 'curved' and plastic == 'elastic':
        return curved_config_elastic
    elif shape == 'curved' and plastic == 'plastic':
        return curved_config_plastic
    elif shape == 'flat' and plastic == 'elastic':
        return flat_config_elastic
    elif shape == 'flat' and plastic == 'plastic':
        return flat_config_plastic
