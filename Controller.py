""" 
Main interface of OVPL with the external world.
Controller interfaces with LabPoolManager and VMPoolManager.

"""

import LabManager
import VMPoolManager

OVPL_LOGGER = logging.getLogger('ovpl')
LOG_FILENAME = 'log/ovpl.log'       # make log name a setting
LOG_FD = open(LOG_FILENAME, 'a')

class Controller:
    def __init__(self):
        pass

    def test_lab(self, lab_id, lab_src_url, version=None):
        try:
            lab_spec = LabManager.get_lab_reqs(lab_id, lab_src_url, version)
        except Exception, e:
            # This should return an error json when Controller is a web service
            return -1
        
        vmpoolmgr = VMPoolManager.VMPoolManager()
        (ip, port) = vmpoolmgr.create_vm(lab_spec)
        LabManager.test_lab(lab_src_url, version, ip, port)

