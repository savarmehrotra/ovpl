start-server:
	python2 ControllerServer.py &
	python2 CentOSVZAdapterServer.py &

stop-server:
	killall python2 #HACK!

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

