"""
    Data Store Get Module
    
    Reads data from the indexed datastore created by mod_ds to return
    requested data to other MQTT clients.

    Module Paramters:
      - ds      : name of mod_ds module that stores data - must be in same json parms
      - sub     : topic for which read requests can be made.
      - buff_cnt: number of rows to read at one time when responding to read requests

    Note that this module uses the "ds" module to read blocks of data.

    Read Requests -
    Other modules can send read requests to the topic defined by "sub". The parameters
    for the read request are in the MQTT message payload as json and define:
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

import json
from ps_mod import PsrpiModule
from ps_parms import PsosParms
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

        self.sub    = self.get_parm("sub",None)
        self.ds     = self.get_parm("ds","ds")
        self.buff_cnt = self.get_parm("buff_cnt",20)

    async def fatal_err(self,msg):
        print(msg)
        await self.log(msg)
        return msg
    
    # Respond to MQTT requests for data
    async def run(self):
        mqtt = self.get_mqtt()

        if self.sub == None:
            return await self.fatal_err( "{} exiting - no subscribe topic (sub) specified".
                                  format(self._name))
        
        self.ds = self.get_svc(self.ds)
        if self.ds == None:
            return await self.fatal_err("{} exiting - ds module {} not found".
                                  format(self._name,self.get_parm("ds","ds")))

        q = asyncio.Queue()
        await mqtt.subscribe(self.sub,q)

        while True:
            data = await q.get()
            await self.read_data(self.ds,data[2])
    
    # Read data from ds from payload
    async def read_data(self,ds,payload):
        if isinstance(payload,str) and payload.startswith('{'):
            try:
                payload = json.loads(payload)
            except:
                return await self.fatal_err("invalid json: {}".format(payload))
        
        if not isinstance(payload,dict):
            return await self.fatal_err("{}: invalid request {}".
                                   format(self._name,payload))
        
        p = PsosParms(payload,self._parms,self.get_defaults())

        resp_topic = p[("resp_topic",None)]
        if resp_topic == None:
            return await self.fatal_err("{}: resp_topic required".format(self._name))

        b = await self.read_blk(ds,p)

        # todo: build and send response
        await self.log("read data: {}".format(b))

    async def read_blk(self,ds,p):
        filter    = p[("filter","#")]
        max_cnt   = p[("max_cnt",10)]
        init_pos  = p.get_parm("init_pos",-1)
        direction = p[("direction","back")]
        
        print("init_pos: {}".format(init_pos))
        if init_pos == -1:
            init_pos = ds.max_idx() - self.buff_cnt
        
        return await ds.read_log_blk(init_pos,max_cnt)
