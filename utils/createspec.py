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
- check out a copy

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
BZR_WORK_AREA = "repo_work_area/bzr/"
GIT_WORK_AREA = "repo_work_area/git/"
SVN_WORK_AREA = "repo_work_area/svn/"


def is_lab_l5(labspec, location):
    """Checks if the lab is integration level 5 from the labspec and if
    the scripts folder exists"""
    print location + "/src/scripts"
    return labspec['lab']['description']['misc']['integration_level'] == 5 and \
            os.path.isdir(location + "/scripts")

def update_l5_info(labspec):
    """Updates the runtime_requirements info for L5 labs in labspec dict"""
    print "Updating L5 info"
    lab_actions = labspec['lab']['runtime_requirements']['platform']['lab_actions']
    lab_actions['init'].append('initialize')
    lab_actions['shutdown'].append('shutdown')
    lab_actions['start'].append('startup')
    lab_actions['backup'].append('backup')
    lab_actions['restore'].append('restore')

def labspec_template():
    """Reads the labspec json file and returns a dict"""
    return json.loads(open("labspec_template.json").read())

def get_redmine_info(lab_id):
    db = MySQLdb.connect("localhost", "", "", "redmine_dump")
    cursor = db.cursor()
    query = """SELECT
            lab_name,
            institute_name,
            discipline,
            dev_status,
            lab_type,
            integration_level,
            dev_os, dev_os_ver,
            dep_os, dep_os_ver,
            disk_space, ram_space
        FROM
            lab_infos
        WHERE
            project_id="%s"
    """ % (lab_id)
    cursor.execute(query)
    lab_info = cursor.fetchall()
    if lab_info:
        return lab_info[0]

def update_spec_from_redmine(labspec, lab_id):
    """Read the redmine database and update the labspec"""
    lab_info = get_redmine_info(lab_id)
    desc = labspec['lab']['description']
    desc['id'] = lab_id
    desc['name'] = lab_info[0].strip()
    desc['developer'][0]['institute'] = lab_info[1].strip()
    desc['discipline'].append(lab_info[2])
    desc['status'] = lab_info[3]
    desc['type'] = lab_info[4]
    desc['misc']['integration_level'] = lab_info[5]
    if lab_info[6]:
        labspec['lab']['build_requirements']['platform']['os'] = lab_info[6]
    if lab_info[7]:
        labspec['lab']['build_requirements']['platform']['osVersion'] = lab_info[7]
    runtime = labspec['lab']['runtime_requirements']['platform']
    if lab_info[8]:
        runtime['os'] = lab_info[8]
    if lab_info[9]:
        runtime['osVersion'] = lab_info[9]
    if lab_info[10]:
        runtime['storage']['min_required'] = lab_info[10]
    if lab_info[11]:
        runtime['memory']['min_required'] = lab_info[11]

def create_labspec():
    labspec = labspec_template()
    update_spec_from_redmine(labspec, lab_id)
    if is_lab_l5(labspec, work_area):
        update_l5_info(labspec)
    print json.dumps(labspec)
    return labspec

def create_spec_for_bzr_repos():
    print BZR_LOCATE
    all_bzr_locations = subprocess.check_output(BZR_LOCATE, shell=True)
    for location in all_bzr_locations.split('\n'):
        # get all the bazaar repo names
        print location
        m = re.match(r'/labs/(\w+\d*)/bzr/([\w\d\-_]+)/', location)
        if m == None:
            continue
        lab_id = m.group(1)
        repo_name = m.group(2)
        work_area = BZR_WORK_AREA + lab_id + "-" + repo_name
        print "Now working on", lab_id, repo_name
        if work_area_exists(work_area):
            update_bzr_working_area(work_area)
        else:
            create_bzr_work_area(location, work_area)
        labspec = create_labspec()
        update_bzr_repo(labspec)

def create_spec_for_git_repos():
    all_git_locations = subprocess.check_output(GIT_LOCATE, shell=True)
    for location in all_git_locations.split('\n'):
        # get all the git repo names 
        m = re.match("/labs/(%s)/" % LAB_ID_REGEX, location)
        if m == None:
            continue
        lab_id = m.group(1)
        for repo_name in os.listdir(location):
            print "Now working on", lab_id, repo_name
            work_area = GIT_WORK_AREA + lab_id + "-" + repo_name
            if work_area_exists(work_area):
                update_git_working_area(work_area)
            else:
                create_git_work_area(location, work_area)
            labspec = create_labspec()
            update_git_repo(labspec)

def create_spec_for_svn_repos():
    all_svn_locations = subprocess.check_output(SVN_LOCATE, shell=True)
    for location in all_svn_locations.split('\n'):
        m = re.match("/labs/(%s)/svn" % LAB_ID_REGEX, location)
        if m == None:
            continue
        lab_id = m.group(1)
        for repo_name in os.listdir(location):
            repo_path = location + "/" + repo_name
            if not os.path.isdir(repo_path):
                continue
            print "Now working on", lab_id, repo_name
            work_area = SVN_WORK_AREA + lab_id + "-" + repo_name
            if work_area_exists(work_area):
                update_svn_working_area(work_area)
            else:
                create_svn_work_area(location, work_area)
            labspec = create_labspec()
            update_svn_repo(labspec)

def work_area_exists(work_area):
    return os.path.isdir(work_area)

def create_bzr_work_area(location, work_area):
    subprocess.check_call("bzr branch %s %s" % (location, work_area), shell=True)

def create_git_work_area(location, work_area):
    subprocess.check_call("git clone %s %s" % (location, work_area), shell=True)

def create_svn_work_area(location, work_area):
    subprocess.check_call("svn co %s %s" % (location, work_area), shell=True)

def update_bzr_working_area(work_area):
    subprocess.check_call("bzr pull -d %s" % work_area, shell=True)

def update_git_working_area(work_area):
    subprocess.check_call("git pull -d %s " % work_area, shell=True)

def update_svn_working_area(work_area):
    subprocess.check_call("svn update -d %s " % work_area, shell=True)

def update_bzr_repo(labspec):
    """Write labspec to a json file. Commit to the working tree and push to parent repo"""
    pass

def update_git_repo(labspec):
    """Write labspec to a json file. Commit to the working tree and push to parent repo"""
    pass

def update_svn_repo(labspec):
    """Write labspec to a json file. Commit to the working tree and push to parent repo"""
    pass

def main():
    create_spec_for_bzr_repos()
    create_spec_for_git_repos()
    create_spec_for_svn_repos()

if __name__ == '__main__':
    main()
