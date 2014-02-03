""" 
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""

#import time

import LabManager
import VMPoolManager
from OVPLLogging import *


class Controller:
    def __init__(self):
        pass

    def test_lab(self, lab_id, lab_src_url, version=None):
        OVPL_LOGGER.debug("Controller.test_lab() for lab ID %s and git url %s" \
                            % (lab_id, lab_src_url))
        try:
            lab_spec = LabManager.get_lab_reqs(lab_id, lab_src_url, version)
            vmpoolmgr = VMPoolManager.VMPoolManager()
            (ip, port) = vmpoolmgr.create_vm(lab_spec)
            #(ip, port) = ("10.4.14.39", "8089")
            vmmgrurl = "http://" + ip
            #time.sleep(10)
            if LabManager.test_lab(vmmgrurl, port, lab_src_url, version):
                return ip
            elif LabManager.test_lab(vmmgrurl, port, lab_src_url, version):
                # retry seems to work (always?)
                return ip
            else:
                OVPL_LOGGER.error("Test failed")
        except Exception, e:
            # This should return an error json when Controller is a web service
            OVPL_LOGGER.error("Test failed with error: " + str(e))


if __name__ == '__main__':
    c = Controller()
    #c.test_lab("asdf", "asdf")
    #print c.test_lab("ovpl01", "https://github.com/nrchandan/vlab-computer-programming")
    print c.test_lab("ovpl01", "https://github.com/avinassh/cse09")
