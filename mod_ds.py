"""
    Data Store Module
    
    Creates an indexed datastore of MQTT messages, similar to MQTT Log.

    Primary file is a list of newline delimited text file rows. Each row
    contains tab delimited fields for date, time, topic and payload.

    The index file consisted of a 4 byte entry for each row in the primary
    file. Each 4 byte entry defines a signed integer with a max value of 2,147,483,647.

    See mod_ds_get for how other MQTT clients can send messages requesting data 
    from this store.

    Module Paramters:
      - sub     : topic to subscribe to - default is "#"
      - fn      : name of primary file
      - fn_idx  : index file name
      - sub_req : topic for which read requests can be made.
    
"""

from ps_mod import PsrpiModule
import asyncio
# import queue
import gc

from ps_util import to_str,to_bytes,file_sz
import ps_util
from ps_subscr import Subscription
import struct
import os
    
# All initialization classes are named ModuleService
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)

        self.sub    = self.get_parm("sub","#")
        self.fn     = self.get_parm("fn","mqtt_dat.txt")
        self.fn_idx = self.get_parm("fn_idx","mqtt_idx.txt")

    # Save all MQTT messages for the defined filter
    async def run(self):
        mqtt = self.get_mqtt()

        q = asyncio.Queue()
        await mqtt.subscribe(self.sub,q)

        while True:
            data = await q.get()
            await self.save_data(data[1],data[2])
    
    # save message
    async def save_data(self,topic,payload):
        self.write_idx()
        
        f = open(self.fn,"a")
        f.write(self.get_dt())
        f.write('\t')
        f.write(to_str(topic))
        f.write('\t')
        
        # remove newline - messes log file
        s = to_str(payload).replace("\\n","↵")
        s = s.replace("\n","↵")
        f.write(s)
        
        f.write('\n')
        f.close()
                        
    # write the current size (next position to write) 
    # as a 4 byte int to the index file
    # IF needed, spi lock should be done before this
    def write_idx(self):
        s = file_sz(self.fn)

        # write 4 bytes to index file
        with open(self.fn_idx,'ab') as f:
            f.write(struct.pack("i",s))

    '''
        EXTERNAL ONLY METHODS
    '''
    def max_idx(self):
        return int(round(file_sz(self.fn_idx)/4) - 1)
    
    # return a block of log file entries starting at number idx,
    # where idx is the number of a line in the log file
    async def read_log_blk(self,idx,cnt):      
        print("idx: {}, cnt: {}".format(idx,cnt))      
        sz = file_sz(self.fn_idx)

        p = idx * 4
        if p > sz:
            return []

        p2 = (0,)
        
        # "rb" = read binary, otherwise error on read
        with open(self.fn_idx,"rb") as f_idx:
            # read this main file position from index file
            f_idx.seek(p)
            p2 = struct.unpack('i', f_idx.read(4))
            
        lines = []
        
        with open(self.fn) as f:
            f.seek(p2[0])
            for ln in f:
                lines.append(ln.rstrip())
                if len(lines) >= cnt:
                    return lines

        return lines
