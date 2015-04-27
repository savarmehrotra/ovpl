ADS
===

Execute the following steps, to configure and then run ADS as a service:

* Edit the file ovpl/config/config.json and,

1. to set the proxies.
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

2. Set the SERVER_IP in LOGSERVER_CONFIGURATION to the IP address of the
machine on which the ADS services are running.

3. Set the COOKIE_SECRET value to some long randomly generated string.

4. Leave the PERSONA_VERIFIER field as it is, if you are using the Mozilla's
default Persona provider service.

5. Change APP_URL field and put the URL where the application is hosted.

6. In the ADAPTER section, change the ADAPTER_NAME to appropriate adapter used.
   Possible values for now are - "CentOSVZAdapter" and "AWSAdapter".


6.1 If using CentOSVZAdapter, edit the file ovpl/src/adapters/settings.py to set
    the following:

    If the services are running on the base machine,
    set ADS_ON_CONTAINER to False.

    If the services are running on a container,
    set ADS_ON_CONTAINER to True.

    Set BASE_IP_ADDRESS = "root@<IP>" where IP is the ip address of
    base machine on which containers are created.

    Set ADS_SERVER_VM_ID to CTID of container running ADS.
    ADS_SERVER_VM_ID = "<CTID>" 

    SUBNET field to match with the subnet of your base machine
    If the ip address of your base machine is 10.2.58.XXX, 
    SUBNET = ["10.2.58.12/28"]


6.2 If using AWSAdapter, copy `src/adapters/sample_aws_config.py` to
    `src/adapters/aws_config.py`, and edit the values accordingly. See
    [here](index.org) for more details.


* Copy `config/sample_authorized_users.py` to `config/authorized_users.py`, and
  add actual email addresses of authorized users.


* As root, go into `src` directory and run make:

```
$ cd src
$ make
```

* To stop the services, or restart:

```
$ cd src
$ make stop-server
$ make restart-server
```

* View the logs at /root/logs/ovpl.log by

```
tail -f /root/logs/ovpl.log
```

* Open the location `http://localhost:8080` from the browser and provide the lab
  id and lab sources url.


* Other related documentation:
Steps to manually create a container
-----
1. vzctl create 101 --ostemplate ubuntu-12.04-custom-x86_64 --ipadd 10.2.58.3 --diskspace 10G:15.0G --hostname cse02.vlabs.ac.in
2. vzctl start 101
3. vzctl set 101 --nameserver inherit --ram 256M --swap 512M --onboot yes --save
