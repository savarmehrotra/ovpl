""" 
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""

#from time import strftime
from datetime import datetime

import LabManager
import VMPoolManager
import Logging
from State import State


class Controller:
    def __init__(self):
        self.system = State.Instance()

    def test_lab(self, lab_id, lab_src_url, revision_tag=None):
        Logging.LOGGER.debug("Controller.test_lab() for lab ID %s and git url %s" \
                            % (lab_id, lab_src_url))
        try:
            lab_spec = LabManager.get_lab_reqs(lab_id, lab_src_url, revision_tag)
            lab_spec['lab_id'] = lab_id
            lab_spec['lab_src_url'] = lab_src_url
            lab_spec['revision_tag'] = revision_tag
            lab_spec['lab']['runtime_requirements']['hosting'] = 'dedicated'
            vmpoolmgr = VMPoolManager.VMPoolManager()
            lab_state = vmpoolmgr.create_vm(lab_spec)
            ip = lab_state['vm_info']['vm_ip']
            port = lab_state['vm_info']['vmm_port']
            vmmgrurl = "http://" + ip
            try:
                if LabManager.test_lab(vmmgrurl, port, lab_src_url, revision_tag):
                    self.update_state(lab_state)
                    return ip
                elif LabManager.test_lab(vmmgrurl, port, lab_src_url, revision_tag):
                    # retry seems to work (always?)
                    self.update_state(lab_state)
                    return ip
                else:
                    Logging.LOGGER.error("Test failed")
            except Exception, e:
                Logging.LOGGER.error("Test failed with error: " + str(e))
            finally:
                self.system.save()
        except Exception, e:
            Logging.LOGGER.error("Test failed with error: " + str(e))

    def update_state(self, state):
        state['lab_history']['released_by'] = 'dummy'
        #state['lab_history']['released_on'] = strftime("%Y-%m-%d %H:%M:%S")
        state['lab_history']['released_on'] = datetime.utcnow()

    def undeploy_lab(self, lab_id):
        Logging.LOGGER.debug("Controller.undeploy_lab for lab_id %s" % lab_id)
        vmpoolmgr = VMPoolManager.VMPoolManager()
        vmpoolmgr.undeploy_lab(lab_id)
        return "Success"


if __name__ == '__main__':
    c = Controller()
    #print c.test_lab("ovpl01", "https://github.com/nrchandan/vlab-computer-programming")
    print c.test_lab("ovpl01", "https://github.com/avinassh/cse09")
