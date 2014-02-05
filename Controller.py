""" 
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""

import pymongo

import LabManager
import VMPoolManager
import Logging


class Controller:
    def __init__(self):
        self.db = pymongo.MongoClient().ovpl
        self.restore_state()

    def restore_state(self):
        """Restores state from a mongodb collection."""
        if "ovpl" in self.db.collection_names():
            self.state = list(self.db.ovpl.find())
        else:
            self.state = []

    def save_state(self):
        #Writes the current state to mongodb(disk)
        if "ovpl" in self.db.collection_names():
            self.db.ovpl.rename("ovpl-last", dropTarget=True)
        self.db.ovpl.insert(self.state)

    def test_lab(self, lab_id, lab_src_url, version=None):
        Logging.LOGGER.debug("Controller.test_lab() for lab ID %s and git url %s" \
                            % (lab_id, lab_src_url))
        def update_state():
            self.state.append({ "lab_id": lab_id,
                                "lab_src_url": lab_src_url,
                                "revision_tag": version,
                                "lab_spec": lab_spec,
                                "vm_ip": ip,
                                "vmm_url": vmmgrurl,
                                "vmm_port": port
                                })
        try:
            lab_spec = LabManager.get_lab_reqs(lab_id, lab_src_url, version)
            lab_spec['lab_id'] = lab_id
            lab_spec['lab_src_url'] = lab_src_url
            vmpoolmgr = VMPoolManager.VMPoolManager()
            (ip, port) = vmpoolmgr.create_vm(lab_spec)
            #(ip, port) = ("10.4.14.39", "8089")
            vmmgrurl = "http://" + ip
            update_state()
            self.save_state()
            if LabManager.test_lab(vmmgrurl, port, lab_src_url, version):
                return ip
            elif LabManager.test_lab(vmmgrurl, port, lab_src_url, version):
                # retry seems to work (always?)
                return ip
            else:
                Logging.LOGGER.error("Test failed")
        except Exception, e:
            # This should return an error json when Controller is a web service
            Logging.LOGGER.error("Test failed with error: " + str(e))


if __name__ == '__main__':
    c = Controller()
    #c.test_lab("asdf", "asdf")
    #print c.test_lab("ovpl01", "https://github.com/nrchandan/vlab-computer-programming")
    print c.test_lab("ovpl01", "https://github.com/avinassh/cse09")
