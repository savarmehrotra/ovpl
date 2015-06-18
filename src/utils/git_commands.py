import os
import json
from __init__ import *
from httplogging.http_logger import logger
from utils.execute_commands import execute_command
from utils.envsetup import EnvSetUp


class LabSpecInvalid(Exception):
    def __init__(self, msg):
        Exception(self, msg)


class GitCommands:

    env = None
    GIT_CLONE_LOC = None
    LAB_SPEC_DIR = None
    LAB_SPEC_FILE = None

    def __init__(self):
        self.env = EnvSetUp.Instance()
        self.GIT_CLONE_LOC = (self.env.get_config_spec())["LABMANAGER_CONFIG"]["GIT_CLONE_LOC"]
        self.LAB_SPEC_DIR = (self.env.get_config_spec())["LABMANAGER_CONFIG"]["LAB_SPEC_DIR"]
        self.LAB_SPEC_FILE = (self.env.get_config_spec())["LABMANAGER_CONFIG"]["LAB_SPEC_FILE"]
        logger.debug("GIT_CLONE_LOC = %s" % str(self.GIT_CLONE_LOC))
        logger.debug("LAB_SPEC_DIR = %s" % str(self.LAB_SPEC_DIR))
        logger.debug("LAB_SPEC_FILE = %s" % str(self.LAB_SPEC_FILE))

    def construct_repo_name(self, lab_src_url):
        # sample lab_src_url: git@github.com:vlead/ovpl.git
        logger.debug("lab_src_url: %s" % lab_src_url)
        repo = lab_src_url.split('/')[-1]
        repo_name = (repo[:-4] if repo[-4:] == ".git" else repo)
        logger.debug("repo_name: %s" % repo_name)
        return str(repo_name)

    def repo_exists(self, repo_name):
        logger.debug("dir = %s" % (self.GIT_CLONE_LOC+repo_name))
        return os.path.isdir(self.GIT_CLONE_LOC+repo_name)

    def clone_repo(self, lab_src_url, repo_name):
        clone_cmd = "git clone %s %s%s" % (lab_src_url, self.GIT_CLONE_LOC,
                                           repo_name)
        logger.debug(clone_cmd)
        try:
            (ret_code, output) = execute_command(clone_cmd)
            logger.debug("Clone repo successful")
        except Exception, e:
            logger.error("Error Cloning the repository: " + str(e))
            raise e

    def pull_repo(self, repo_name):
        pull_cmd = "git --git-dir=%s/.git pull" % (self.GIT_CLONE_LOC +
                                                   repo_name)
        logger.debug("pull cmd: %s" % pull_cmd)
        try:
            (ret_code, output) = execute_command(pull_cmd)
            logger.debug("Pull repo successful")
        except Exception, e:
            logger.error("Error Pulling the repository: " + str(e))
            raise e

    def reset_repo(self, repo_name):
        reset_cmd = "git --git-dir=%s/.git reset --hard" % (self.GIT_CLONE_LOC
                                                            + repo_name)
        logger.debug("reset cmd: %s" % reset_cmd)
        try:
            (ret_code, output) = execute_command(reset_cmd)
            logger.debug("reset repo successful")
        except Exception, e:
            logger.error("Error Resetting the repository: " + str(e))
            raise e

    def checkout_version(self, repo_name, version=None):
        if version:
            checkout_cmd = "git --git-dir=%s checkout %s" \
                           % ((self.GIT_CLONE_LOC + repo_name), version)
            try:
                (ret_code, output) = execute_command(checkout_cmd)
                logger.debug("Checkout repo successful")
            except Exception, e:
                logger.error("Error checking out the repository: " + str(e))
                raise e

    def get_spec_path(self, repo_name):
        return self.GIT_CLONE_LOC + repo_name + self.LAB_SPEC_DIR

    def get_lab_spec(self, repo_name):
        spec_file_path = self.get_spec_path(repo_name) + self.LAB_SPEC_FILE
        logger.debug("spec_file_path: %s" % spec_file_path)
        if not os.path.exists(spec_file_path):
            logger.error("Lab spec file not found")
            raise LabSpecInvalid("Lab spec file not found")
        try:
            return json.loads(open(spec_file_path).read())
        except Exception, e:
            logger.error("Lab spec JSON invalid: " + str(e))
            raise LabSpecInvalid("Lab spec JSON invalid: " + str(e))


if __name__ == '__main__':
    git = GitCommands()
    lab_src_url = "https://github.com/Virtual-Labs/computer-programming-iiith.git"
    try:
        repo_name = git.construct_repo_name(lab_src_url)
        if git.repo_exists(repo_name):
            #  reset_repo(repo_name)
            git.pull_repo(repo_name)
        else:
            git.clone_repo(lab_src_url, repo_name)
            git.checkout_version(repo_name, None)
    except Exception, e:
        logger.debug(str(e))
