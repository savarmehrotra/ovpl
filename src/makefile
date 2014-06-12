test: stop-server
	python2 adapters/AdapterServer.py &
	@#python2 VMManager/VMManagerServer.py &
	python2 ControllerServer.py &

start-server:
	python2 adapters/AdapterServer.py &
	python2 Controller.py &
	
stop-server:
	-killall python2 #HACK!

server-ip:
	@ps aux | grep py

restart-server: stop-server start-server


start-mongodb:
	service mongod start

repair-mondodb:
	service mongod stop
	mongod --repair
	#INCOMPLETE
	service mongod start

