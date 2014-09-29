ovpl
====

1) Edit the file ovpl/config/config.json to set the proxies
  
   "ENVIRONMENT": {
       "HTTP_PROXY":"proxy.vlabs.ac.in:8080",
       "HTTPS_PROXY":"proxy.vlabs.ac.in:8080"
   },

2) Do the same with the file ovpl/src/VMManager/config.json

3) Edit the file ovpl/src/settings.py to set the 
   SUBNET field to match with the subnet of your base machine

   If the ip address of your base machine is 10.2.58.XXX, 
         
	SUBNET = ["10.2.58.12/28"]

4) Do the same with the file ovpl/src/adapters/settings.py