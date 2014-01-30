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

import subprocess

from LabActionsRunner import LabActionsRunner

GIT_CLONE_LOC = "./"
VMM_LOGGER = logging.getLogger('VMM')
LOG_FILENAME = 'log/vmmanager.log'       # make log name a setting
LOG_FD = open(LOG_FILENAME, 'a')

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

def test_lab(lab_src_url, version=None):
    # check out the source with version provided
        # is repo already exists? if yes, then do a git pull
        # else clone the repo
    # get the labspec from /scripts/lab_spec.json
    # get the appropriate the actions from lab_spec.json
    # run LabAction Runner
        # instantiate the object

    def get_build_spec(lab_spec):
        return {"build_steps": lab_spec['lab'][u'build_requirements']['platform']['build_steps']}

    def get_installer_steps_spec(lab_spec):
        return {"installer": lab_spec['lab']['build_requirements']['platform']['installer']}

    def construct_repo_name():
        repo = lab_src_url.split('/')[-1]
        repo_name = repo[:-4] if repo[-4:] == ".git" else repo
        return repo_name

    def repo_exists(repo_name):
        return os.path.isdir(GIT_CLONE_LOC+repo_name)

    def clone_repo(repo_name):
        clone_cmd = shlex.split("git clone %s" % lab_src_url)
        try:
            subprocess.check_call(clone_cmd, stdout=LOG_FD, stderr=LOG_FD)
        except Exception, e:
            # different logger needs to be implemented here
            VMM_LOGGER.error("git clone failed: %s %s" % (repo_name, str(e)))
            raise e

    def pull_repo(repo_name):
        pull_cmd = shlex.split("git --git-dir=%s pull" % \
                            (GIT_CLONE_LOC + repo_name))
        try:
            subprocess.check_call(pull_cmd, stdout=LOG_FD, stderr=LOG_FD)
        except Exception, e:
            VMM_LOGGER.error("git pull failed: %s %s" % (repo_name, str(e)))
            raise e

    def checkout_version(repo_name):
        if version:
            try:
                checkout_cmd = shlex.split("git --git-dir=%s checkout %s" \
                                    % ((GIT_CLONE_LOC + repo_name), version))
                subprocess.check_call(checkout_cmd, stdout=LOG_FD, stderr=LOG_FD)
            except Exception, e:
                VMM_LOGGER.error("git checkout failed for repo %s tag %s: %s" \
                                    % (repo_name, version, str(e)))
                raise e

    def get_lab_spec(repo_name):
        repo_path = GIT_CLONE_LOC + repo_name + LAB_SPEC_LOC
        if not os.path.exists(repo_path):
            raise LabSpecInvalid("Lab spec file not found")
        try:
            return json.loads(open(repo_path).read())
        except Exception, e:
            raise LabSpecInvalid("Lab spec JSON invalid: " + str(e))

    repo_name = construct_repo_name()
    if repo_exists(repo_name):
        pull_repo(repo_name)
    else:
        clone_repo(repo_name)
    checkout_version(repo_name)

    lab_spec = get_lab_spec(repo_name)

    lar = LabActionsRunner(get_installer_steps_spec(lab_spec), "")
    lar.run_install_source()

    lar = LabActionsRunner(get_build_steps_spec(lab_spec), "")
    lar.run_build_steps()


def setup_logging():
    VMM_LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    handler = logging.handlers.TimedRotatingFileHandler(
                                LOG_FILENAME, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    VMM_LOGGER.addHandler(handler)


if __name__ == "__main__":
    print cpu_load()
    print mem_usage()