#!/bin/bash

# the array contains the list of service *names*
# the actual service corresponding to the name is below
SERVICES=("LOGGER" "ADAPTER" "CONTROLLER")

LOGGER='src/httplogging/http_logging_server.py'
ADAPTER='src/adapters/adapter_server.py'
CONTROLLER='src/controller_server.py'

#PID_FILE='/var/run/ads.pid'
PID_FILE='ads.pid'

# Correct usage of the script and its valid
# arguments.
usage() {
  echo -e "usage: ./manage_services.sh \t\t\t start all services"
  echo -e "   or: ./manage_services.sh [action] \t\t perform action on all services "
  echo -e "   or: ./manage_services.sh [action] [services]  perform action on specified service(s)\n"
  echo -e "Action:"
  echo -e "start \t start service(s)"
  echo -e "stop  \t stop service(s)\n"
  echo -e "Services:"
  echo -e "LOGGER"
  echo -e "ADAPTER"
  echo -e "CONTROLLER"
}

# Utility function: to check if a given array contains a given value
in_array() {
  local n=$#
  local value=${!n}
  for ((i=1; i < $#; i++)) {
    if [ "${!i}" == "${value}" ]; then
      # in shell 0 is success
      echo 0
      exit 0
      #return 0
    fi
  }
  echo 1
  #return 1
  exit 1
}

# Utility function: to get status of various services
status() {
  for record in `cat $PID_FILE`; do
    process_name=`echo $record | cut -d ":" -f 1`
    pid=`echo $record | cut -d ":" -f 2`
    if [[ $process_name == $service ]]; then
      echo -e "\e[33m$service exists in pid file, now checking if
      it is alive\e[0m"
      ps -ef | grep ${!service} | grep -v grep  
      if [ $? == 0 ]; then
        echo -e "\e[32m$service service is already running\e[0m"
	exit 1;
      else
        echo -e "\e[31m$service service was stopped unexpectedly. Process 
        with $pid pid is dead. Removing it from pid file now...\e[0m"
	sed -i /$process_name/d $PID_FILE
      fi      
    fi
  done  
}

# Start the services.
start_service() {
  if [[ ! -f $PID_FILE ]]; then
    touch $PID_FILE
  fi
  # If no specific services are mentioned,
  # start all the services.
  if [ -z "$args" ]; then
    echo -e "\e[33mStarting all services.\e[0m"
    for service in ${SERVICES[@]}; do
      status "$service"
      # from the service get the actual service to start
      python ${!service} &
      # enter the pid of the service in our pid file
      # The variable "$!" has the PID of the last
      # background process started.
      echo "$service:$!" >> $PID_FILE
      sleep 1
    done
    exit 0;

  else
    # Start the specific services mentioned
    # by the user.
    for service in $args; do
      if [[ $(in_array "${SERVICES[@]}" "$service") != 0 ]]; then
        echo -e "\e[31mInvalid service name: $service.\e[0m"
        usage
        exit 1;
      else
	status "$service"
        # Since the services ex. LOGGER are stored inside input arguments, it
        # is tricky to extract a variable name from a variable.  This has been
        # done here using "${!arg}" syntax. Refer
        # http://www.linuxquestions.org/questions/programming-9/bash-how-to-get-variable-name-from-variable-274718/
        # for more.
        python ${!service} &
        echo "$service:$!" >> $PID_FILE
        sleep 1
      fi
    done
  fi
}

# Stop the services.
stop_service() {
  # If no specific service is mentioned,
  # stop all the services.
  if [ -z "$args" ]; then
    if [ -f $PID_FILE ]; then
      for i in `cat $PID_FILE`; do
        pid=`echo $i | cut -d ":" -f 2`
        kill $pid
      done
      rm $PID_FILE
      echo -e "\e[32mStopped all services.\e[0m"
    else
      echo -e "\e[33mNo services are running to be stopped.\e[0m"
    fi

  else
    # Stop only the service(s) mentioned by
    # the user.
    for arg in $args; do
      if [ -f $PID_FILE ]
      then
        for process in `cat $PID_FILE`; do
          process_name=`echo $process | cut -d ":" -f 1`
          pid=`echo $process | cut -d ":" -f 2`
          if [[ $process_name == $arg ]]; then
            kill $pid;
            echo -e "\e[33mStopping service $arg.\e[0m"
            sed -i /$process_name/d $PID_FILE
            echo -e "\e[32mService stopped.\e[0m"
          fi
        done
      else
        echo -e "\e[33mNo services are running to be stopped.\e[0m"
      fi
    done
  fi
}

# Start mongod service.
start_mongod() {
  service mongod start
}

# Stop mongod service.
stop_mongod() {
  service mongod stop
}

# Repair mongod service.
repair_mongod() {
  mongod --repair
}

# Check if the service mongod is already running.
pre_check() {
  service mongod status
  if [ $? != 0 ]
  then
    echo -e '\e[31mservice mongod is not running\e[0m'
    stop_mongod
    echo -e '\e[33mstopping mongod\e[0m'
    repair_mongod
    echo -e '\e[33mrestarting mongod\e[0m'
    start_mongod
    echo -e '\e[32mservice mongod successfully restarted\e[0m'
  fi
}

# If the script is executed alone, all the services
# are started.
if [ $# == 0 ]; then
  pre_check
  start_service
  exit 0;

# This is the help option, to view the correct
# usage of the script and its valid arguments.
elif [[ $1 == "-h" || $1 == "--help" ]]; then
  usage
  exit 0;

# If arguments are greater than or equal to 1
# other than help. This means that the user has
# entered specific services to be started/stopped.
else
  input_args=($@)
  action=${input_args[0]}
  args=${input_args[@]:1}

  if [ "$action" == "start" ]; then
    pre_check
    start_service "$args"
    exit 0;

  elif [ "$action" == "stop" ]; then
    stop_service "$args"
    exit 0;

  else
    echo -e "\e[31mError: Invalid action.\e[0m"
    usage
    exit 1;
  fi
fi
