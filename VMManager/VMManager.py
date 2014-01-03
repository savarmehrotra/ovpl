# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" An interface for managing VMs for a selected platform. """

import subprocess

# Run this command for me, please.
# how long has your VM been running?
# what is your memory footprint?
# what is your diskspace footprint?
# what processes are currently running?
# what is your CPU load?


# UGLY DUCK PUNCHING: Backporting check_output from 2.7 to 2.6
if "check_output" not in dir(subprocess):
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = f

def execute(command):
    # do some validation
    return subprocess.check_output(command, shell=True)

def running_time():
    return execute("uptime")

def mem_usage():
    return execute("free -mg")

def disk_usage():
    return execute("df -h")

def running_processes():
    return execute("ps -e -o command")

def cpu_load():
    return execute("ps -e -o pcpu | awk '{s+=$1} END {print s\"%\"}'")


if __name__ == "__main__":
    print cpu_load()
    print mem_usage()
