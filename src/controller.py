"""
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""


from datetime import datetime
from __init__ import *
from lab_manager import LabManager
from vm_pool_manager import VMPoolManager
from state import State
from httplogging.http_logger import logger
from utils.git_commands import GitCommands


class Controller:
    state = None
    lab_spec = None
    lab_vm_details = None
    labmgr = None
    vmpoolmgr = None
    git = None

    def __init__(self):
        self.state = State.Instance()
        self.lab_spec = {}
        self.lab_vm_details = {}
        self.labmgr = LabManager()
        self.vmpoolmgr = VMPoolManager()
        self.git = GitCommands()

    def test_lab(self, current_user, lab_id, lab_src_url, revision_tag=None):
        logger.debug("test_lab() for lab ID %s and git url %s"
                     % (lab_id, lab_src_url))
        try:
            self.lab_spec = self.labmgr.get_lab_reqs(lab_src_url,
                                                     revision_tag)
            self.update_lab_spec(self.lab_spec, lab_id, lab_src_url,
                                 revision_tag)
            logger.debug("test_lab(); invoking create_vm() on vmpoolmgr")
            self.lab_vm_details = self.vmpoolmgr.create_vm(self.lab_spec)
            logger.debug("test_lab(): Returned from VMPool = %s" %
                         (str(self.lab_vm_details)))
            ip = self.lab_vm_details['vm_info']['vm_ip']
            port = self.lab_vm_details['vm_info']['vmm_port']
            vmmgrurl = "http://" + ip
            logger.debug("test_lab(): vmmgrurl = %s" % (vmmgrurl))
            try:
                (ret_val, ret_str) = self.labmgr.test_lab(vmmgrurl,
                                                          port,
                                                          lab_src_url,
                                                          revision_tag)
                if(ret_val):
                    self.update_lab_vm_details(current_user)
                    logger.info("test_lab(): test succcessful, ip = %s" % ip)
                    return ip
                else:
                    logger.error("test_lab(); Test failed with error:" +
                                 str(ret_str))
                    return "Test failed: See log file for errors"
            except Exception, e:
                logger.error("test_lab(); Test failed with error: " + str(e))
                return "Test failed: See log file for errors"
                """ TODO: Garbage collection clean up for the created VM """
            finally:
                logger.debug("finally block, lab_id = %s" % lab_id)
                self.state.save(self.lab_vm_details)
        except Exception, e:
            logger.debug("except  block, lab_id = %s" % lab_id)
            logger.error("test_lab(): Test failed with error: " + str(e))
            return "Test failed: See log file for errors"

    def update_lab_spec(self, lab_spec, lab_id, lab_src_url, revision_tag):
        lab_spec['lab']['description']['id'] = lab_spec['lab_id'] = lab_id
        lab_spec['lab_src_url'] = lab_src_url
        lab_spec['lab_repo_name'] = self.git.construct_repo_name(lab_src_url)
        lab_spec['revision_tag'] = revision_tag
        lab_spec['lab']['runtime_requirements']['hosting'] = 'dedicated'
        logger.debug("lab_repo_name: %s" % (lab_spec['lab_repo_name']))

    def update_lab_vm_details(self, current_user):
        self.lab_vm_details['lab_history']['deployed_by'] = current_user
        self.lab_vm_details['lab_history']['released_by'] = 'dummy'
        self.lab_vm_details['lab_history']['released_on'] = datetime.utcnow()

    def undeploy_lab(self, lab_id):
        logger.debug("undeploy_lab for lab_id %s" % lab_id)
        self.vmpoolmgr.undeploy_lab(lab_id)
        return "Success"

if __name__ == '__main__':
    c = Controller()
    lab_src_url = "https://github.com/Virtual-Labs/computer-programming-iiith.git"
    #    print c.test_lab("travula@gmail.com", "cse02", url)
    vmmgrurl = "http://172.16.0.2"
    port = "8000"
    revision_tag = None
    labmgr = LabManager()
    try:
        (ret_val, ret_str) = labmgr.test_lab(vmmgrurl,
                                             port,
                                             lab_src_url,
                                             revision_tag)
    except Exception, e:
        logger.error("test_lab(); Test failed with error: " + str(e))
