"""
    Log Service Class
    
    Logs messages.
    
"""

from ps_mod import PsrpiModule
import asyncio

# All initialization classes are named PsrpiModule
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.pub = parms.get_parm("pub_log","log")
        
    async def run(self):
        self.mqtt = self.get_mqtt()
    
    async def log_msg(self,name,msg):
        
        log_msg = name + ": " + msg
        
        if self.mqtt == None:
            print("no mqtt:",log_msg)
        else:
            # await mqtt.publish(self._pub_topic,log_msg)
            print("sending mqtt msg:",self.pub,log_msg)
            await self.mqtt.publish(self.pub,log_msg)
