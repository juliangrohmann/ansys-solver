import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v3.configs import kwsst_curved_config_elastic
from analysis_v3.configs import kwsst_flat_config_elastic
from analysis_v3.configs import curved_config_elastic
from analysis_v3.configs import curved_config_plastic
from analysis_v3.configs import flat_config_elastic
from analysis_v3.configs import flat_config_plastic


def get_config(shape, plastic):
    if shape == 'curved' and plastic == 'elastic':
        return curved_config_elastic
    elif shape == 'curved' and plastic == 'plastic':
        return curved_config_plastic
    elif shape == 'flat' and plastic == 'elastic':
        return flat_config_elastic
    elif shape == 'flat' and plastic == 'plastic':
        return flat_config_plastic
    elif shape == 'kwsst_flat' and plastic == 'elastic':
        return kwsst_flat_config_elastic
    elif shape == 'kwsst_curved' and plastic == 'elastic':
        return kwsst_curved_config_elastic
