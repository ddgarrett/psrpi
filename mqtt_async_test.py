import asyncio
import asyncio_mqtt as aiomqtt

import config
import ps_util as util

'''
    Per https://pypi.org/project/asyncio-mqtt
    Windows users can not use the default async ProactorEventLoop.
'''
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("not windows")
    pass

async def main():
    async with aiomqtt.Client("10.0.0.231") as client:
        async with client.messages() as messages:
            await client.subscribe("#")
            async for message in messages:
                print("{} {}".format(message.topic,util.to_str(message.payload)))
                '''
                if message.topic.matches("humidity/outside"):
                    print(f"[humidity/outside] {message.payload}")
                if message.topic.matches("+/inside"):
                    print(f"[+/inside] {message.payload}")
                if message.topic.matches("temperature/#"):
                    print(f"[temperature/#] {message.payload}")
                '''


asyncio.run(main())