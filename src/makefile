test: stop-server
	python httplogging/http_logging_server.py &
	python2 adapters/adapter_server.py &
	python2 controller_server.py &

start-server:
	python httplogging/http_logging_server.py &
	sleep 1
	python2 adapters/adapter_server.py &
	sleep 1
	python2 controller_server.py &

stop-server:
	-killall python2 #HACK!
	-killall python #HACK!

server-ip:
	@ps aux | grep py

restart-server: stop-server start-server


start-mongodb:
	service mongod start

repair-mondodb:
	service mongod stop
	mongod --repair
	service mongod start
