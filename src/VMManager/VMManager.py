# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" An interface for managing VMs for a selected platform. """

# Run this command for me, please.
# how long has your VM been running?
# what is your memory footprint?
# what is your diskspace footprint?
# what processes are currently running?
# what is your CPU load?

# to do : handle exceptions

import os
import subprocess
import shlex
import json
import __init__
from http_logging.http_logger import logger

from LabActionRunner import LabActionRunner

GIT_CLONE_LOC = "/root/"
LAB_SPEC_LOC = "/scripts/labspec.json"

class LabSpecInvalid(Exception):
    def __init__(self, msg):
        Exception(self, msg)


# Backporting check_output from 2.7 to 2.6
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
    try:
        logger.info("Command executed: " + command)
        return subprocess.check_output(command, shell=True)
    except Exception, e:
        logger.error("Execution failed: " + str(e))
        return "Error executing the command: " + str(e)

def running_time():
    logger.info("Command executed: uptime")
    return execute("uptime")

def mem_usage():
    logger.info("Command executed: free -mg")
    return execute("free -mg")

def disk_usage():
    logger.info("Command executed: df -h")
    return execute("df -h")

def running_processes():
    logger.info("Command executed: ps -e -o command")
    return execute("ps -e -o command")

def cpu_load():
    logger.info("Command executed: ps -e -o pcpu")
    return execute("ps -e -o pcpu | awk '{s+=$1} END {print s\"%\"}'")

def test_lab(lab_src_url, version=None):
    # check out the source with version provided
        # is repo already exists? if yes, then do a git pull
        # else clone the repo
    # get the labspec from /scripts/lab_spec.json
    # get the appropriate the actions from lab_spec.json
    # run LabAction Runner
        # instantiate the object
    from envsetup import EnvSetUp
    e = EnvSetUp()
    logger.info("Environment http_proxy = %s" % os.environ["http_proxy"])
    logger.info("Environment https_proxy = %s" % os.environ["https_proxy"])

    def fill_aptconf():

        try:
            http_proxy = os.environ["http_proxy"]
            https_proxy = os.environ["https_proxy"]
            http_cmd = r'echo "Acquire::http::Proxy \"%s\";"%s'%(http_proxy, '>>/etc/apt/apt.conf')
            https_cmd = r'echo "Acquire::https::Proxy \"%s\";"%s'%(https_proxy, '>>/etc/apt/apt.conf')
            subprocess.check_call(http_cmd, shell=True)
            subprocess.check_call(https_cmd, shell=True)
        except Exception, e:
            logger.error("Writing to /etc/apt/apt.conf failed with error: %s" % (str(e)))
            raise e

        
    def get_build_steps_spec(lab_spec):
        return {"build_steps": lab_spec['lab']['build_requirements']['platform']['build_steps']}

    def get_build_installer_steps_spec(lab_spec):
        return {"installer": lab_spec['lab']['build_requirements']['platform']['installer']}

    def get_runtime_installer_steps(lab_spec):
        return {"installer": lab_spec['lab']['runtime_requirements']['platform']['installer']}

    def get_runtime_actions_steps(lab_spec):
        return lab_spec['lab']['runtime_requirements']['platform']['lab_actions']

    def construct_repo_name(lab_id, lab_src_url):
        logger.debug("lab_src_url: %s" % lab_src_url)
        repo = lab_src_url.split('/')[-1]
        repo_name = lab_id + (repo[:-4] if repo[-4:] == ".git" else repo)
        logger.debug("repo_name: %s" % repo_name)
        return repo_name

    def repo_exists(repo_name):
        return os.path.isdir(GIT_CLONE_LOC+repo_name)

    def clone_repo(repo_name):
        clone_cmd = "git clone %s %s%s" % (lab_src_url, GIT_CLONE_LOC,repo_name)
        logger.debug(clone_cmd)
        try:
            subprocess.check_call(clone_cmd, shell=True)
        except Exception, e:
            logger.error("git clone failed for repo %s: %s" % (repo_name, str(e)))
            raise e

    def pull_repo(repo_name):
        pull_cmd = "git --git-dir=%s/.git pull" % (GIT_CLONE_LOC + repo_name)
        logger.debug(pull_cmd)
        try:
            subprocess.check_call(pull_cmd, shell=True)
        except Exception, e:
            logger.error("git pull failed for repo %s: %s" % (repo_name, str(e)))
            raise e

    def checkout_version(repo_name):
        if version:
            try:
                checkout_cmd = shlex.split("git --git-dir=%s checkout %s" \
                                    % ((GIT_CLONE_LOC + repo_name), version))
                logger.debug(checkout_cmd)
                subprocess.check_call(checkout_cmd, shell=True)
            except Exception, e:
                logger.error("git checkout failed for repo %s tag %s: %s" \
                                    % (repo_name, version, str(e)))
                raise e

    def get_lab_spec(repo_name):
        repo_path = GIT_CLONE_LOC + repo_name + LAB_SPEC_LOC
        if not os.path.exists(repo_path):
            logger.error("Lab spec file not found")
            raise LabSpecInvalid("Lab spec file not found")
        try:
            return json.loads(open(repo_path).read())
        except Exception, e:
            logger.error("Lab spec JSON invalid: " + str(e))
            raise LabSpecInvalid("Lab spec JSON invalid: " + str(e))

    logger.info("Starting test_lab")
    fill_aptconf()
    repo_name = construct_repo_name("cse02", lab_src_url)
    logger.debug("repo name = %s" % repo_name)
    if repo_exists(repo_name):
        pull_repo(repo_name)
    else:
        clone_repo(repo_name)
    checkout_version(repo_name)

    lab_spec = get_lab_spec(repo_name)
    try:
        dir_path = GIT_CLONE_LOC+repo_name+"/scripts"
        os.chdir(dir_path)
        logger.debug("Changed to Diretory: %s" % dir_path)
        logger.debug("CWD: %s" % str(os.getcwd()))

        lar = LabActionRunner(get_build_installer_steps_spec(lab_spec))
        lar.run_install_source()

        lar = LabActionRunner(get_build_steps_spec(lab_spec))
        lar.run_build_steps()

        lar = LabActionRunner(get_runtime_installer_steps(lab_spec))
        lar.run_install_source()

        lar = LabActionRunner(get_runtime_actions_steps(lab_spec))
        lar.run_init_lab()
        lar.run_start_lab()
        logger.info("Finishing test_lab: Success")
        return "Success"
    except Exception, e:
        logger.error("VMManager.test_lab failed: " + str(e))
        return "Test lab failed"


if __name__ == "__main__":
    test_lab("https://bitbucket.org/virtual-labs/cse02-programming.git")
    print cpu_load()
    print mem_usage()
