"""
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""


from datetime import datetime
from __init__ import *
from lab_manager import LabManager
from vm_pool_manager import VMPoolManager
from state import State
from http_logging.http_logger import logger
from utils import git_commands


class Controller:
    state = None
    lab_spec = None
    lab_vm_details = None
    labManager = None
    vmpoolmgr = None

    def __init__(self):
        self.state = State.Instance()
        self.lab_spec = {}
        self.lab_vm_details = {}
        self.labmgr = LabManager()
        self.vmpoolmgr = VMPoolManager()

    def test_lab(self, current_user, lab_id, lab_src_url, revision_tag=None):
        logger.debug("test_lab() for lab ID %s and git url %s"
                     % (lab_id, lab_src_url))
        try:
            self.lab_spec = self.labManager.get_lab_reqs(lab_src_url,
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
                (ret_val, ret_str) = self.labManager.test_lab(vmmgrurl,
                                                              port,
                                                              lab_src_url,
                                                              revision_tag)
                if(ret_val):
                    self.update_lab_vm_details(current_user)
                    logger.info("test_lab(): test succcessful")
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
                self.state.save(self.lab_vm_details)
        except Exception, e:
            logger.error("test_lab(): Test failed with error: " + str(e))
            return "Test failed: See log file for errors"

    def update_lab_spec(self, lab_spec, lab_id, lab_src_url, revision_tag):
        lab_spec['lab']['description']['id'] = lab_spec['lab_id'] = lab_id
        lab_spec['lab_src_url'] = lab_src_url
        lab_spec['lab_repo_name'] = git_commands.construct_repo_name(
            lab_src_url)
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
    url = "https://github.com/Virtual-Labs/data-structures-iiith.git"
    print c.test_lab("cse02", url)
