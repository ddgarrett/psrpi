"""  ***micropython compatible***

    Load Configuration File and Configure sys.path
    
    To set path config and access config.json values:
    
        import config
        cfg = config.cfg
    
    The above code loads the config.json file into the
    a dictionary named cfg and extends the sys.path.
    
    config.py must be in root directory.
    
    This module can also be used in micropython.
"""

try:
    import ujson as json
except ModuleNotFoundError:
    import json

import sys

# load a json file
# here because we can't use the psos_util
# until after loading config.json
def load_json_config(fn):
    # read the paramter file
    with open(fn) as f:
        parms = json.load(f)
        f.close()
        return parms
    
    return None

# read main configuration file
cfg = load_json_config("config.json")
print("boot: config",cfg)

# extend module search path
if "path" in cfg:
    sys.path.extend(cfg["path"]) 

