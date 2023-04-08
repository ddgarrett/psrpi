"""
    Data Store Module
    
    Creates an indexed datastore of MQTT messages, similar to MQTT Log.

    Primary file is a list of newline delimited text file rows. Each row
    contains tab delimited fields for date, time, topic and payload.

    The index file consisted of a 4 byte entry for each row in the primary
    file. Each 4 byte entry defines a signed integer with a max value of 2,147,483,647.

    Other MQTT clients can send messages requesting data from this store.

    Module Paramters:
      - sub     : topic to subscribe to
      - fn      : name of primary file
      - fn_idx  : index file name
      - sub_req : topic for which read requests can be made.
      - buff_cnt: number of rows to read at one time when responding to read requests

    Read Requests -
    Other modules can send read requests to the topic defined by "sub_req". The parameters
    for the read request are in the MQTT message payload and define:

        - resp_topic : topic to use in sending the response - required
        - filter     : filter to use in reading data. Default is "#"
        - max_cnt    : maximum number or rows to return. Default is 10.
        - min_cnt    : minimum number of rows to try to return. Default is 0.
        - init_pos   : initial row number in the file, -1 for start at last row, 0 for first row. Default is -1.
        - direction  : direction to read, "fwd" or "back" (forward or backward). Default is "back"
        - follow     : forward updates to the file to resp_topic? true or false. Default is false.

    The module will read starting at the init_pos, reading forward or backward in the file
    starting at "init_pos". Only rows which match the specified "resp_topic" will be returned up to a maximum
    of "max_cnt" rows. If fewer than the optional "min_cnt" rows are found, the read direction will be reversed
    and matching rows will be added to the response until "max_cnt" rows are read or end or beginning of file
    is reached. Response will be an array of rows, each row being an array with date, time, topic and payload.
    
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
    
'''
    MQTT Log Published Messages Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)

        self.sub    = self.get_parm("sub","#")
        self.fn     = self.get_parm("fn","mqtt_dat.txt")
        self.fn_idx = self.get_parm("fn_idx","mqtt_idx.txt")


    # Save all MQTT messages for the defined filter
    async def run(self):
        # TODO: start process to handle read requests
        mqtt = self.get_mqtt()

        # while mqtt._client == None:
        #   await ps_util.sleep_ms(100)

        # print("mod_ds subscribing to {}".format(self.sub))

        q = asyncio.Queue()
        await mqtt.subscribe(self.sub,q)

        while True:
            data = await q.get()
            await self.save_dat(data[1],data[2])
    
    # save message
    async def save_dat(self,topic,payload):
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

        # if fowarding msg, send to each matching subscriber
        '''
        if len(self.subs) > 0:
            # print("...forwarding {} {}".format(topic,payload))
            await self.local_callback(topic,s)
        '''
            
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
        with open(self.fn_idx,'ab') as f:
            f.write(struct.pack("i",s))

    # return the log file entry number idx, where idx is the number
    # of a line in the log file
    async def read_log_entry(self,idx):
        if self.fn_idx == None:
            return None
        
        sz = file_sz(self.fn_idx)

        p = idx * 4
        if p > sz:
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

        return ln

    # Add subscriber to a given topic
    async def subscribe(self,topic_filter,resp_topic):

        # todo: start subprocess for each queue?
        '''        
        sub = Subscription(topic_filter,queue,0)
        self.subs.append(sub)
        '''
            
        # give other tasks a chance to run
        await ps_util.sleep_ms(0)
    
    # remove all of the subscriptions for a given resp_topic?
    # cancel any tasks started for the resp_topic?
    async def unsubscribe(self,queue):
        pass
