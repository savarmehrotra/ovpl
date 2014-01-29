import json
import re
import os
import subprocess
import shlex
from exception import Exception

GIT_CLONE_LOC = "./lab-repo-cache/"
OVPL_LOGGER = logging.getLogger('ovpl')
LOG_FILENAME = 'log/ovpl.log'       # make log name a setting
LOG_FD = open(LOG_FILENAME, 'a')
LAB_SPEC_LOC = "/scripts/labspec.json"

class LabSpecInvalid(Exception):
    def __init__(self, msg):
        Exception(self, msg)

def get_lab_reqs(lab_id, lab_src_url, version=None):
    # sample lab_src_url: git@github.com:vlead/ovpl.git
    def construct_repo_name():
        repo = url.split('/')[-1]
        repo_name = lab_id + (repo[:-4] if repo[-4:] == ".git" else repo)
        return repo_name

    def repo_exists(repo_name):
        return os.path.isdir(GIT_CLONE_LOC+repo_name)

    def clone_repo(repo_name):
        clone_cmd = shlex.split("git clone %s" % lab_src_url)
        try:
            subprocess.check_call(clone_cmd, stdout=LOG_FD, stderr=LOG_FD)
        except Exception, e:
            OVPL_LOGGER.error("git clone failed: %s %s" % (repo_name, str(e)))
            raise e

    def pull_repo(repo_name):
        pull_cmd = shlex.split("git --git-dir=%s pull" % \
                            (GIT_CLONE_LOC + repo_name))
        try:
            subprocess.check_call(pull_cmd, stdout=LOG_FD, stderr=LOG_FD)
        except Exception, e:
            OVPL_LOGGER.error("git pull failed: %s %s" % (repo_name, str(e)))
            raise e

    def checkout_version(repo_name):
        if version:
            try:
                checkout_cmd = shlex.split("git --git-dir=%s checkout %s" \
                                    % ((GIT_CLONE_LOC + repo_name), version))
                subprocess.check_call(checkout_cmd, stdout=LOG_FD, stderr=LOG_FD)
            except Exception, e:
                OVPL_LOGGER.error("git checkout failed for repo %s tag %s: %s" \
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

    return get_lab_spec(repo_name)
    #vm_spec = json.loads(open("vmspec.json", "r").read())

def test_lab(lab_id, lab_src_url, version=None):
    pass


def setup_logging():
    OVPL_LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    handler = logging.handlers.TimedRotatingFileHandler(
                                LOG_FILENAME, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    OVPL_LOGGER.addHandler(handler)

