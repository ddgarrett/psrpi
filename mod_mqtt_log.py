"""
    MQTT Log Class - Logs MQTT
    
    This service createa an indexed
    log file which can then be read as an indexed array. Methods
    write the index file, return number of entries in main file,
    and allow access to main file via an array of index numbers.

    Indexed log file is create if the "fn_idx" parm specifies a file name.

    Note that care must be taken to keep the two files in sync. NO checking
    is done (yet). Could have re-index option which runs if index file is 
    gone or the last entry in the idx does not point to the end of the log
    file. This would require reading line by line through the main file
    and creating a 4 byte entry in the index file for each line in the log
    file.
    
    When acting in this mode, other services can "subscribe" to this service mqtt_log,
    to receive notification that a new record has been received. This service will then
    forward the message to any subscribers who have subscribed to the topic.
    
    
"""

from ps_mod import PsrpiModule
import asyncio
import queue
import gc

from ps_util import to_str,to_bytes,file_sz
from ps_subscr import Subscription
import struct
import os
    
'''
    MQTT Log Published Messages Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.fn = self.get_parm("log_fn","mqtt_log.txt")
        self.print = self.get_parm("print",True)

        self.fn_idx = self.get_parm("idx_fn",None)

        self.subs = [] # if we are forwarding msg
        

    # if a subscription topic is specified, we log all of
    # the received info to the log file then forward
    # the info to any other services which have subscribed
    # to the topic.
    async def run(self):
        sub = self.get_parm("sub",None)
        if sub == None:
            return
        
        mqtt = self.get_mqtt()
        
        # Can not be running as the main MQTT service
        # if we are forwarding messages.
        if self == mqtt:
            return
        
        q = queue.Queue()
        await mqtt.subscribe(sub,q)
        while True:
            data = await q.get()
            await self.publish(data[1],data[2])
    
    # Subscribe to a given topic
    async def subscribe(self,topic_filter,queue,qos=0):
        # logging might cause loop?
        # await self.log("sub mqtt log {}".format(topic_filter))
        
        sub = Subscription(topic_filter,queue,qos)
        self.subs.append(sub)
            
        # give other tasks a chance to run
        await asyncio.sleep_ms(0)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        
        if self.print:
            print("svc_mqtt_log publish:",to_str(topic),to_str(payload))
  
        if self.fn != None:
                        
            if self.fn_idx != None:
                self.write_idx()
            
            f = open(self.fn,"a")
            f.write(self.get_dt())
            f.write('\t')
            f.write(to_bytes(topic))
            f.write('\t')
            
            # remove newline - messes log file
            s = to_str(payload).replace("\\n","↵")
            s = s.replace("\n","↵")
            f.write(to_bytes(s))
            
            f.write('\n')
            f.close()

        # if fowarding msg, send to each matching subscriber
        if len(self.subs) > 0:
            # print("...forwarding {} {}".format(topic,payload))
            await self.local_callback(topic,payload)
            
    # forward messages to local subscribers
    async def local_callback(self,topic,msg):        
        t = to_str(topic)
        m = to_str(msg)
        
        # don't think this would happen,
        # but just in case...
        if t.startswith('local/'):
            t = t[6:]
        
        t_split = t.split('/')
        
        for s in self.subs:
            s.put_match(t_split,t,m)        
            
    # write the current size (next position to write) 
    # as a 4 byte int to the index file
    # IF needed, spi lock should be done before this
    def write_idx(self):
        s = file_sz(self.fn)

        # write 4 bytes to index file
        with open(self.fn_idx,'a') as f:
            f.write(struct.pack("i",s))

    # return number of enties in the main file.
    # this is simply the length of the index file / 4
    async def log_len(self):
        s = file_sz(self.fn_idx)
        return int(s/4)

    # return the log file entry number idx, where idx is the number
    # of a line in the log file
    async def read_log_entry(self,idx):
        if self.fn_idx == None:
            return None
        
        await self.lock_spi()
        sz = file_sz(self.fn_idx)

        p = idx * 4
        if p > sz:
            self.unlock_spi()
            return None

        p2 = -1
        
        # "rb" = read binary, otherwise error on read
        with open(self.fn_idx,"rb") as f_idx:
            # read this main file position from index file
            f_idx.seek(p)
            p2 = struct.unpack('i', f_idx.read(4))
            
        with open(self.fn) as f:
            f.seek(p2[0])
            ln = f.readline().strip()

        self.unlock_spi()
        return ln

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        pass
    
    async def lock_spi(self):
        if self.spi_svc != None:
            await self.spi_svc.lock()
            
    def unlock_spi(self):
        if self.spi_svc != None:
            self.spi_svc.unlock()
        