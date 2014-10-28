ovpl
====


Edit the file ovpl/config/config.json and 
                 ovpl/src/VMManager/config.json 
   to set the proxies. 
```
    "ENVIRONMENT": {
        "HTTP_PROXY":"http://proxy.vlabs.ac.in:8080",
        "HTTPS_PROXY":"http://proxy.vlabs.ac.in:8080"
    },
```
   if no proxies are used, 
```
    "ENVIRONMENT": {
        "HTTP_PROXY":"",
        "HTTPS_PROXY":""
    },
```


Edit the file ovpl/src/adapters/settings.py to set the 
   SUBNET field to match with the subnet of your base machine

    If the ip address of your base machine is 10.2.58.XXX, 
    SUBNET = ["10.2.58.12/28"]

Run as a root. Ensure no make is run.

```
python ovpl/src/http_logging/http_logging_server.py &
```
```
python2 ovpl/src/ControllerServer.py &
```
```
python2 ovpl/src/adapters/AdapterServer.py &
```

View the logs at /root/logs/ovpl.log by

```
tail -f /root/logs/ovpl.log
```

Open the location `http://localhost:8080` from the browser and
   provide the lab id and lab sources url.


Steps to manually create a container
====
1. vzctl create 101 --ostemplate ubuntu-12.04-custom-x86_64 --ipadd 10.2.58.3 --diskspace 10G:15.0G --hostname cse02.vlabs.ac.in
2. vzctl start 101
3. vzctl set 101 --nameserver inherit --ram 256M --swap 512M --onboot yes --save
