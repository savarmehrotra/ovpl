# move to the top level dir
# to start the http looger
cd ../src/
python http_logging/http_logging_server.py &
# run the test cases
cd ..
python -m tests.test_openvz_adapter

