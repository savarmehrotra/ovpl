ovpl
====


1. Edit the file ovpl/config/config.json and 
                 ovpl/src/VMManager/config.json 
   to set the proxies. 

    "ENVIRONMENT": {
        "HTTP_PROXY":"http://proxy.vlabs.ac.in:8080",
        "HTTPS_PROXY":"http://proxy.vlabs.ac.in:8080"
    },

   if no proxies are used, 
    
    "ENVIRONMENT": {
        "HTTP_PROXY":"",
        "HTTPS_PROXY":""
    },


2. Do the same with the file ovpl/src/VMManager/config.json

3. Edit the file ovpl/src/settings.py to set the 
   SUBNET field to match with the subnet of your base machine

    If the ip address of your base machine is 10.2.58.XXX, 
    SUBNET = ["10.2.58.12/28"]

4. Do the same with the file ovpl/src/adapters/settings.py

5. change to source directory (ovpl/src ) and run make.
   % make

6. Open the location http://localhost:8080 from the browser and
   provide the lab id and lab sources url.

7. You can check the logs at ovpl/log/ovpl.log, and ovpl/log/centosadapter.log on the base machine.
   The log on the container will be at /root/VMManager/log/vmmanager.log

Steps to manually create a container
====
1. vzctl create 101 --ostemplate ubuntu-12.04-custom-x86_64 --ipadd 10.2.58.3 --diskspace 10G:15.0G --hostname cse02.vlabs.ac.in
2. vzctl start 101
3. vzctl set 101 --nameserver inherit --ram 256M --swap 512M --onboot yes --save


