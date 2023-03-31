"""
    Timer Module Class
    
    Trigger an even every n seconds

    pub_msg = message to publish
    pub_topics = [list] of topics to publish to
    pub_wait   = number of seconds to wait between publishing
    
    Service will wait 10ms between publishing so it doesn't send
    too many messages in a short period of time.
    
"""

from ps_mod import PsrpiModule
import asyncio
import ps_util
import time


# All initialization classes are named ModuleService
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)
        
    async def run(self):
        
        mqtt   = self.get_mqtt()
        
        # parameters
        topics = self.get_parm("pub_topics",[])
        msg    = self.get_parm("pub_msg",[])
        wait = self.get_parm("pub_wait",5*60)
        wait_ms   = wait*1000
        initial_wait_ms = self.get_parm("init_wait",wait)*1000
        sleep     = self.get_parm("sleep_ms",10)
        
        # function aliases 
        ticks_add = ps_util.ticks_add
        ticks_ms  = ps_util.ticks_ms
        sleep_ms  = ps_util.sleep_ms       
       
        next_time = ticks_add(ticks_ms(),initial_wait_ms)
        
        while True:
            print("sleeping {}ms".format(ticks_add(next_time,-ticks_ms())))
            await sleep_ms(ticks_add(next_time,-ticks_ms()))
            next_time = ticks_add(next_time,wait_ms)
            
            for i in range(len(topics)):
                if i >= len(msg):
                    m = ""
                else:
                    m = msg[i]
                    
                await mqtt.publish(topics[i],m)
                await sleep_ms(sleep)
