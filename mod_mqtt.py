"""
    MQTT Class
    
    Class that connects to MQTT and supports
    publish and subscribe.
    
    Other services use this service to publish and subscribe to MQTT. 
    
    Notes:
    1. If topic begins with "local/" this service
       a. removes the "local/" prefix
       b. forwards the message to any services subscribing to the topic
       c. does not forward the message the global MQTT broker
       
    2. If there is no wifi service or the wifi service has not yet connected
       or this service has not yet connected to the MQTT broker,
       it will forward published messages to any subscribed service.
       
       Note that this allows MQTT subscribe/publish to be used without an MQTT broker.
       This can be useful for testing since it allows running the test without
       waiting for WiFi and the MQTT broker. This also allows PSOS to be run on
       microcontrollers without WiFi such as the original Raspberry Pi Pico.

"""

from ps_mod import PsrpiModule
import asyncio
import binascii
import ps_secrets
import queue
from ps_util import to_str, to_bytes
import sys
import time
import gc
import asyncio_mqtt as aiomqtt
# import utf8_char


# from ps_subscription import Subscription

# make root ca part of this module
_hivemq_root_ca =  """-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
"""
    
'''
    MQTT Class
    
'''
# All initialization classes are named PsrpiModule
class ModuleService(PsrpiModule):
    
    def __init__(self, parms):
        super().__init__(parms)    
        
        self._client = None
        self._subscriptions = []       
        self.wifi    = self.get_svc("wifi")
        self._msg_buff = []

    def mqtt_callback(self,topic,msg):
        if self._in_buff(topic,msg):
            return
        
        t = to_str(topic)
        m = to_str(msg)
        
        t_split = t.split('/')
        
        for subscr in self._subscriptions:
            subscr.put_match(t_split,t,m)
            
    # check if we recently received the the same topic and buffer.
    # This deals with duplicate messages received due to the
    # RPi400 Mosquitto MQTT broker bridge with HiveMQ
    def _in_buff(self,topic,msg):
        # remove any messages in buffer older than 3 seconds
        t = time.ticks_ms()
        while len(self._msg_buff) > 0:
            if time.ticks_diff(t,self._msg_buff[0][0]) > 3000:
                self._msg_buff.pop(0)
            else:
                break
                
        for i in range(len(self._msg_buff)):
            b = self._msg_buff[i]
            if b[1] == topic and b[2] == msg:
                return True
            
        # msg not in buff, add it
        self._msg_buff.append([t,topic,msg])
        return False
        
    async def run(self):

        async with aiomqtt.Client("10.0.0.231") as client:
            async with client.messages() as messages:
                await client.subscribe("#")
                async for message in messages:
                    print("{} {}".format(message.topic,to_str(message.payload)))

    
    
    '''
    # Subscribe to a given topic
    # Payloads received for the topic are placed on queue.
    # Tasks can therefore just go into a wait
    # until a payload to be written to a queue.
    async def subscribe(self,topic_filter,queue,qos=0):
        await self.log("subscr " + topic_filter)
        
        sub = Subscription(topic_filter,queue,qos)
        self._subscriptions.append(sub)
        if self._client != None:
            sub.subscribe(self._client)
            
        # give other tasks a chance to run
        await uasyncio.sleep(0)

    # when first connected or after reconnect
    # resubscribe to all previous subscriptions
    async def resubscribe(self):
        for sub in self._subscriptions:
            await self.log("resubscr " + to_str(sub._filter))
            sub.subscribe(self._client)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        # if local topic, only send to local services
        if topic.startswith('local/'):
            if self.get_parm("print_local",False):
                print("pub local: ",topic[6:],payload)
            self.mqtt_callback(to_bytes(topic[6:]),to_bytes(payload))
        else:
            if self._client != None:
                self._client.publish(to_bytes(topic), to_bytes(payload),retain,qos)
                
            # go ahead and publish locally
            else:
                self.mqtt_callback(to_bytes(topic),to_bytes(payload))
                
        # give other tasks a chance to run
        await uasyncio(0)

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        for s in self._subscriptions:
            if s._queue == queue:
                self._subscriptions.remove(s)
                
'''
