# PSRPi
Based on concepts developed on the PSOS project. Like the PSOS project, Publish / Subscribe for Raspberry Pi (PSRPi) is a framework that supports incremental development of complex python systems using simple python modules. Key features include:
- Simple to learn and use
- Easily extensible through simple to develop reusable modules
- Low overhead

To run:
1. Install Paho MQTT client  > pip install paho-mqtt
2. Install asyncio-mqtt      > pip install asyncio-mqtt

Notes:
1. config.json is in the .gitignore so it won't be updated from different source. 
You can create a local one using this as an example:
    ```json
        {"cust": "cust", 
        "sys": "win01",
        "sha": "none", 
        "fn_parms": "win01_parms.json", 
        "parms": "parms", 
        "path": ["base"]
        }
    ```

Thing to use this framework for:
1. an MQTT smart bridge 
    a. elminate duplicates 
    b. use lan/ topic prefix 
    c. call mod_bridge
    d. cache messages sent in last x seconds to elimate duplicates

2. web server to monitor/control devices

3. save and maybe serve up, MQTT messages via filter, count, start position
    a. call mod_log_srch

4. trigger to periodically generate messages **DONE***
    - mod_timer

5. access/update MongoDB - either local or remote

6. generalized web sockets interface to MQTT?

