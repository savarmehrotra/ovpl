import json
import re
import os
import subprocess
import shlex
from exceptions import Exception
import requests

import Logging

GIT_CLONE_LOC = "./lab-repo-cache/"
LAB_SPEC_LOC = "/scripts/labspec.json"
TEST_LAB_API_URI = '/api/1.0/test-lab'

class LabSpecInvalid(Exception):
    def __init__(self, msg):
        Exception(self, msg)

def get_lab_reqs(lab_id, lab_src_url, version=None):
    # sample lab_src_url: git@github.com:vlead/ovpl.git
    def construct_repo_name(lab_id, lab_src_url):
        repo = lab_src_url.split('/')[-1]
        repo_name = lab_id + (repo[:-4] if repo[-4:] == ".git" else repo)
        return repo_name

    def repo_exists(repo_name):
        return os.path.isdir(GIT_CLONE_LOC+repo_name)

    def clone_repo(repo_name):
        clone_cmd = shlex.split("git clone %s %s%s" % (lab_src_url, GIT_CLONE_LOC, repo_name))
        try:
            subprocess.check_call(clone_cmd, stdout=Logging.LOG_FD, stderr=Logging.LOG_FD)
        except Exception, e:
            Logging.LOGGER.error("git clone failed: %s %s" % (repo_name, str(e)))
            raise e

    def pull_repo(repo_name):
        # dirty hack to fix git pull
        pull_cmd = shlex.split("git --git-dir=%s/.git pull" % \
                            (GIT_CLONE_LOC + repo_name))
        try:
            subprocess.check_call(pull_cmd, stdout=Logging.LOG_FD, stderr=Logging.LOG_FD)
        except Exception, e:
            Logging.LOGGER.error("git pull failed: %s %s" % (repo_name, str(e)))
            raise e

    def checkout_version(repo_name):
        if version:
            try:
                checkout_cmd = shlex.split("git --git-dir=%s checkout %s" \
                                    % ((GIT_CLONE_LOC + repo_name), version))
                subprocess.check_call(checkout_cmd, stdout=Logging.LOG_FD, stderr=Logging.LOG_FD)
            except Exception, e:
                Logging.LOGGER.error("git checkout failed for repo %s tag %s: %s" \
                                    % (repo_name, version, str(e)))
                raise e

    def get_lab_spec(repo_name):
        # Allow no lab spec but not an invalid json as a lab spec
        spec_path = GIT_CLONE_LOC + repo_name + LAB_SPEC_LOC
        if not os.path.exists(spec_path):
            raise LabSpecInvalid("Lab spec file not found")
        try:
            return json.loads(open(spec_path).read())
        except Exception, e:
            raise LabSpecInvalid("Lab spec JSON invalid: " + str(e))

    Logging.LOGGER.debug("LabManager.get_lab_reqs()")
    repo_name = construct_repo_name(lab_id, lab_src_url)
    if repo_exists(repo_name):
        pull_repo(repo_name)
    else:
        clone_repo(repo_name)
    checkout_version(repo_name)
    return get_lab_spec(repo_name)
    #vm_spec = json.loads(open("vmspec.json", "r").read())

def test_lab(vmmgr_ip, port, lab_src_url, version=None):
    # make sure VM Manager is running
    # the target VM should have LabActionRunner scripts 
    # VM Manager should do the following?
    # or better it should invoke another script which should
        # clone the repo in the VM
        # get the lab_spec
        # run Lab Action Runner
    Logging.LOGGER.debug("LabManager.test_lab()")
    payload = {"lab_src_url": lab_src_url, "version": version}
    url = '%s:%s%s' % (vmmgr_ip, port, TEST_LAB_API_URI)
    response = requests.post(url=url, data=payload)
    return "Success" in response.text
