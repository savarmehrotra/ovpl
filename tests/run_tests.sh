# move to the top level dir
# to start the http looger
cd ../src/
python httplogging/http_logging_server.py &
# run the test cases
cd ..
python -m tests.test_centos_openvz_adapter
python -m tests.test_aws_adapter
python -m tests.test_centos_bridged_adapter
# stop the logging server
cd src/
make stop-server

