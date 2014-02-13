"""
This script creates the labspec.json file for all labs using information from
the developer portal and checks in the json file along with the sources.

General approach:
- Check out a repository to get a working area
- Read the redmine info for the lab and update labspec.json
- if "scripts" folder exists and level is 5, add runtime info for labspec
- create a new commit 
- update the repo

1. for bzr repos:
- No need to check out as server has working area

2. for git repo:
- need to validate

3. for svn repo:
- check out a copy at the working directory
"""

import json
import subprocess
import re
import os
import MySQLdb

PATH = "/labs"
GIT_LOCATE = r"find %s -maxdepth 3 -name %s -exec du -sh {} \; | grep -v '^4.0K' | cut -f2" % (PATH, "git")
BZR_LOCATE = r"find %s -maxdepth 5 -name %s -exec du -sh {} \; | grep -v '^4.0K' | cut -f2" % (PATH, "trunk")
SVN_LOCATE = r"find %s -maxdepth 3 -name %s -exec du -sh {} \; | grep -v '^4.0K' | cut -f2" % (PATH, "svn")
LAB_ID_REGEX = r"\w+\d*"


def is_lab_l5(labspec, location):
    """Checks if the lab is integration level 5 from the labspec and if
    the scripts folder exists"""
    pass

def update_l5_info(labspec):
    """Updates the runtime_requirements info for L5 labs in labspec dict"""
    pass

def labspec_template():
    """Reads the labspec json file and returns a dict"""
    return json.loads(open("labspec_template.json").read())

def update_redmine_info(labspec, lab_name):
    """Read the redmine database and update the labspec"""
    pass

def create_spec_for_bzr_repos():
    print BZR_LOCATE
    all_bzr_locations = subprocess.check_output(BZR_LOCATE, shell=True)
    for location in all_bzr_locations.split('\n'):
        # get all the bazaar repo names
        print location
        m = re.match(r'/labs/(\w+\d*)/bzr/([\w\d\-_]+)/', location)
        if m == None:
            continue
        lab_name = m.group(1)
        repo_name = m.group(2)
        print "Now working on", lab_name, repo_name
        update_bzr_branch(location)
        labspec = labspec_template()
        update_redmine_info(labspec, lab_name)
        if is_lab_l5(labspec, location):
            update_l5_info(labspec)
        update_bzr_repo()
    
def update_bzr_repo():
    """Commit to the working tree and push to parent repo"""
    pass

def update_bzr_branch(location):
    subprocess.check_call("bzr update " + location, shell=True)

def create_spec_for_git_repos():
    pass

def create_spec_for_svn_repos():
    pass

def main():
    create_spec_for_bzr_repos()
    create_spec_for_git_repos()
    create_spec_for_svn_repos()

if __name__ == '__main__':
    main()
