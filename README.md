# PSRPi
Based on concepts developed on the PSOS project. Like the PSOS project, Publish / Subscribe for Raspberry Pi (PSRPi) is a framework that supports incremental development of complex python systems using simple python modules. Key features include:
- Simple to learn and use
- Easily extensible through simple to develop reusable modules
- Low overhead

To run:
1. Install Paho MQTT client  > pip install paho-mqtt
2. Install asyncio-mqtt      > pip install asyncio-mqtt

Thing to use this framework for:
1. an MQTT smart bridge (elminate duplicates - use lan/ topic prefix)
    - mod_bridge
2. web server to monitor/control devices
3. save and maybe serve up, MQTT messages via filter, count, start position
    - mod_log_srch
4. trigger to periodically generate messages (like e01 "svc_pub_timer" does now)
    - mod_timer
5. access/update MongoDB - either local or remote
6. generalized web sockets interface to MQTT?

