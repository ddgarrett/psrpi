"""
    1. create new instance of each service modules
    2. start each of the services,
    3. enter loop but currently do nothing
        
    Services are defined in config["fn_parms"]
    
    Mqtt service is required to connect to an MQTT broker.
    
    Other services call mqtt to subscribe to topics
    and publish to topics.
    
    Mqtt polls for new messages to subscribed topics
    and forwards any messages via a queue associated with
    each subscription.
    
"""

import asyncio
import os
import gc
import ps_util
from ps_parms import PsosParms



async def main(parms,config):
        
    # globally accessible default parameters
    defaults = {}
    if "defaults" in parms:
        defaults = parms["defaults"]
    
    # perform a one time conversion of any {...} in
    # defaults using config valus
    ps_util.format_defaults(defaults,config)
    gc.collect()
    
    # globally accessible service instances
    services = {}
    defaults["services"] = services
    defaults["config"]   = config
    defaults["started"]  = False
    
    defaults["sysname"]  = os.name
    
    print("main: init services")
    gc.collect()
    
    # if services is a string
    # read the file by that name
    svc = parms["services"]
    
    if type(svc) == str:
        if '{' in svc:
            svc = svc.format(**defaults)
        svc = ps_util.load_parms(config,svc)
    
    for svc_parms in svc:
        
        gc.collect()

        # create module specific parms object
        psos_parms = PsosParms(svc_parms,defaults,config)
        
        # create a new instance of a service
        # and store as a service under specified name
        name = svc_parms["name"]
        module_name = svc_parms["module"]
        
        print("... ",name)
        module = __import__(module_name)
        services[name] =  module.ModuleService(psos_parms)
          
        
    print("main: run services")
        
    for svc_parms in parms["services"]:
        gc.collect()
        name = svc_parms["name"]
        svc  = services[name]
        # print("... " + name)
        asyncio.create_task(svc.run())

        
    defaults["started"] = True
    
    while True:
        # nothing to do here, but can't return?
        
        # could create a queue that no one writes to and wait?
        # or use that queue as an optional print queue?
        # or restart subscription? or stats subscription? or ?
                    
        # allow co-routines to execute
        # print("main: free space "+str(gc.mem_free()))
        gc.collect()
        await asyncio.sleep(5)
        
        
