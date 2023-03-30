"""
    Boot up PS RPi (Publish/Subscribe Raspberry Pi)
    
    Read parameter file to start up clients.
"""

try:
    import ujson as json
    import uasyncio as asyncio
except ModuleNotFoundError:
    import json
    import asyncio

import gc
import sys

# below configures the os.path
import config
cfg = config.cfg

# now that we have path configured
# we can import psos_util
import ps_util

# read parms
pfn = cfg["fn_parms"]
parms = ps_util.load_parms(cfg,pfn)

# start main
if "name" in parms:
    print("boot:",parms["name"])
          
main_name = parms["main"]
print("boot: starting " + main_name)

'''
    Per https://pypi.org/project/asyncio-mqtt
    Windows users can not use the default async ProactorEventLoop.
'''
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("not windows")
    pass

main = __import__(main_name)
asyncio.run(main.main(parms,cfg))
