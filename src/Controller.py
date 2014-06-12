""" 
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""

#from time import strftime
from datetime import datetime
import time

import LabManager
import VMPoolManager
import Logging
from State import State


class Controller:
    def __init__(self):
        self.system = State.Instance()
        lab_spec = {}

    def test_lab(self, lab_id, lab_src_url, revision_tag=None):
        Logging.LOGGER.debug("Controller.test_lab() for lab ID %s and git url %s" \
                            % (lab_id, lab_src_url))
        try:
            lab_spec = LabManager.get_lab_reqs(lab_id, lab_src_url, revision_tag)
            self.update_lab_spec(lab_spec, lab_id, lab_src_url, revision_tag)
            if lab_spec['lab']['runtime_requirements']['hosting'] == 'dedicated':
               """ TODO: Undeploy , fnd proper place to invoke undeploy""" 
               self.undeploy_lab(lab_id)
            vmpoolmgr = VMPoolManager.VMPoolManager()
            Logging.LOGGER.debug("Controller: test_lab(); invoking create_vm() on vmpoolmgr")
            lab_state = vmpoolmgr.create_vm(lab_spec)
            Logging.LOGGER.debug("Controller: test_lab(): Returned from VMPool = %s" % (str(lab_state)))
            ip = lab_state['vm_info']['vm_ip']
            port = lab_state['vm_info']['vmm_port']
            vmmgrurl = "http://" + ip
            Logging.LOGGER.debug("Controller: test_lab(): vmmgrurl = %s" % (vmmgrurl))
            try:
                (ret_val, ret_str) = LabManager.test_lab(vmmgrurl, port, lab_src_url, revision_tag)
                if(ret_val):
                    self.update_state(lab_state)
                    Logging.LOGGER.info("Controller: test_lab(): test succcessful")
                    return ip
                else:
                    Logging.LOGGER.error("Controller: test_lab(); Test failed with error:" + str(ret_str))
                    return "Test failed: See log file for errors"
            except Exception, e:
                Logging.LOGGER.error("Controller: test_lab(); Test failed with error: " + str(e))
                return "Test failed: See log file for errors"
                """ TODO: Garbage collection clean up for the created VM """ 
            finally:
                self.system.save()
        except Exception, e:
            Logging.LOGGER.error("Controller: test_lab(): Test failed with error: " + str(e))
            return "Test failed: See log file for errors"

    def update_lab_spec(self, lab_spec, lab_id, lab_src_url, revision_tag):
        lab_spec['lab']['description']['id'] = lab_spec['lab_id'] = lab_id
        lab_spec['lab_src_url'] = lab_src_url
        lab_spec['revision_tag'] = revision_tag
        lab_spec['lab']['runtime_requirements']['hosting'] = 'dedicated'

    def update_state(self, state):
        state['lab_history']['released_by'] = 'dummy'
        #state['lab_history']['released_on'] = strftime("%Y-%m-%d %H:%M:%S")
        state['lab_history']['released_on'] = datetime.utcnow()
        self.system.state.append(state)

    def undeploy_lab(self, lab_id):
        Logging.LOGGER.debug("Controller.undeploy_lab for lab_id %s" % lab_id)
        vmpoolmgr = VMPoolManager.VMPoolManager()
        vmpoolmgr.undeploy_lab(lab_id)
        return "Success"


if __name__ == '__main__':
    c = Controller()
    #print c.test_lab("ovpl01", "https://github.com/nrchandan/vlab-computer-programming")
    #print c.test_lab("ovpl01", "https://github.com/avinassh/cse09")
    print c.test_lab("cse02", "git@bitbucket.org:virtuallabs/cse02-programming.git")
    #print c.test_lab("cse08", "http://10.4.14.2/cse08.git")
    #print c.test_lab("ovpl01", "https://github.com/vlead/ovpl")
    #print c.test_lab("ovpl01", "https://github.com/avinassh/cse09")
    #print c.test_lab("cse30", "https://github.com/avinassh/cse09")
    #print c.undeploy_lab("ovpl01")
    #print c.undeploy_lab("cse30")
