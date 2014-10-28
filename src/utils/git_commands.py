import os
import subprocess
import json
import __init__
from http_logging.http_logger import logger
from envsetup import EnvSetUp

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

current_file_path = os.path.dirname(os.path.abspath(__file__))
config_spec = json.loads(open(current_file_path + "/../../config/config.json").read())
GIT_CLONE_LOC =  config_spec["LABMANAGER_CONFIG"]["GIT_CLONE_LOC"]
LAB_SPEC_DIR =  config_spec["LABMANAGER_CONFIG"]["LAB_SPEC_DIR"]
LAB_SPEC_FILE =  config_spec["LABMANAGER_CONFIG"]["LAB_SPEC_FILE"]
logger.debug("GIT_CLONE_LOC = %s" % str(GIT_CLONE_LOC))
logger.debug("LAB_SPEC_DIR = %s" % str(LAB_SPEC_DIR))
logger.debug("LAB_SPEC_FILE = %s" % str(LAB_SPEC_FILE))

e = EnvSetUp()	

class LabSpecInvalid(Exception):
    def __init__(self, msg):
        Exception(self, msg)

# sample lab_src_url: git@github.com:vlead/ovpl.git
def construct_repo_name(lab_src_url):
    logger.debug("lab_src_url: %s" % lab_src_url)
    repo = lab_src_url.split('/')[-1]
    repo_name = (repo[:-4] if repo[-4:] == ".git" else repo)
    logger.debug("repo_name: %s" % repo_name)
    return repo_name

def repo_exists(repo_name):
    return os.path.isdir(GIT_CLONE_LOC+repo_name)

def clone_repo(lab_src_url, repo_name):
    clone_cmd = "git clone %s %s%s" % (lab_src_url, GIT_CLONE_LOC,repo_name)
    logger.debug(clone_cmd)
    logger.debug("http_proxy: %s" % os.environ['http_proxy'])
    logger.debug("https_proxy: %s" % os.environ['https_proxy'])
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

def reset_repo(repo_name):
    logger.debug("reset_cmd = %s" % (GIT_CLONE_LOC + repo_name))
    reset_cmd = "git --git-dir=%s/.git reset --hard" % (GIT_CLONE_LOC + repo_name)
    logger.debug("reset_cmd: %s" % (reset_cmd))
    try:
        subprocess.check_call(reset_cmd, shell=True)
    except Exception, e:
        logger.error("git reset failed: %s %s" % (repo_name, str(e)))
        raise e

def checkout_version(repo_name, version=None):
    if version:
        try:
            checkout_cmd = "git --git-dir=%s checkout %s" \
                % ((GIT_CLONE_LOC + repo_name), version)
            logger.debug("checkout_cmd: %s" % checkout_cmd)
            subprocess.check_call(checkout_cmd, shell=True)
        except Exception, e:
            logger.error("git checkout failed for repo %s tag %s: %s" \
                % (repo_name, version, str(e)))
            raise e

def get_spec_path(repo_name):
    return GIT_CLONE_LOC + repo_name + LAB_SPEC_DIR

def get_lab_spec(repo_name):
    spec_file_path = get_spec_path(repo_name) + LAB_SPEC_FILE
    logger.debug("spec_file_path: %s" % spec_file_path)
    if not os.path.exists(spec_file_path):
        logger.error("Lab spec file not found")
        raise LabSpecInvalid("Lab spec file not found")
    try:
        return json.loads(open(spec_file_path).read())
    except Exception, e:
        logger.error("Lab spec JSON invalid: " + str(e))
        raise LabSpecInvalid("Lab spec JSON invalid: " + str(e))
