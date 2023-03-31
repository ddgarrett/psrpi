"""
    PSOS Service Class
    
    Superclass of all PSOS Services
    
"""

import asyncio
import json

import time

import ps_util
import gc

class PsrpiModule:
    
    def __init__(self, parms):
        self._parms   = parms
        self._name    = self.get_parm("name")
                
        self.tz       = self.get_parm("tz",-8)
        self.dev      = self.get_parm("dev","?")
        
    # get a parameter value
    # return default if parameter not specified
    def get_parm(self,name,default=None):
        return self._parms.get_parm(name,default)
    
    # get a named PSOS service
    def get_svc(self,name):
        return self._parms.get_svc(name)
    
    # return mqtt service
    def get_mqtt(self):
        return self.get_svc("mqtt")
                
    # get formatted date and time
    def get_dt(self):
        t = time.localtime(time.mktime(time.localtime()))
        return "{1}/{2}/{0} {3}:{4:02d}:{5:02d}".format(*t)
    
    def get_defaults(self):
        return self._parms._defaults
    
    def get_config(self):
        return self._parms.get_config()
               
           
    # Reset microcontroller
    # If there is a service named "reset"
    # will use that service.reset() method.
    # Otherwise just use machine.reset()
    def reset(self,rsn=None):
        
        if rsn != None:
            self.display_lcd_msg(str(rsn))
            
            fname = self.get_parm("log_file",None)
            if fname != None:
                f = open(fname,"a")
                f.write(self.get_dt())
                f.write('\t')
                f.write(rsn)
                f.write('\n')
                f.close()
            
        svc = self.get_svc("reset")
        if svc != None:
            svc.reset(rsn)
            time.sleep(5) # in case reset is not immediate
        else:
            print("resetting system: ", rsn)
            time.sleep(5) # give print time to run before resetting
            quit()  # no reset, so we'll just quit
            time.sleep(5) # in case reset is not immediate

    # if a log service has been defined
    # write a message to the log
    async def log(self,msg):
        log = self.get_svc("log")
         
        if log != None:
            await log.log_msg(self._name,msg)
        else:
            print(self._name,":",str(msg))
    
    # default run method - just return
    async def run(self):
        pass
        



