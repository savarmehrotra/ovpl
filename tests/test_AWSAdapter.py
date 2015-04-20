import unittest
import json
import requests

from src.adapters.AWSAdapter import AWSAdapter
from src.LabManager import get_lab_reqs

vm_id = None
vm_ip = None
vm_mgr_port = None

class TestAWSAdapter(unittest.TestCase):
    def setUp(self):
        # hardcoded paths are not flexible. this will only work if I run it from
        # the top-level of ovpl directory..
        self.lab_spec = json.loads(open("scripts/labspec.json").read())
        self.adapter = AWSAdapter()
	self.repo_name = "ovpl"
        get_lab_reqs("https://github.com/vlead/ovpl.git")

    def test_create_vm(self):
        global vm_id
        vm_id = self.adapter.create_vm(self.lab_spec)
        vm_ip = self.adapter.get_vm_ip(vm_id)
        instance = self.adapter.get_instance(vm_id)
        print vm_ip
        print vm_id
        print instance
        print instance.state_code
        print "state code represents that instance is pending"

        self.assertIn(instance.state_code, (0, 16))

    def test_init_vm(self):
	global vm_ip
        global vm_mgr_port
        result = self.adapter.init_vm(vm_id, self.repo_name)
        print result
        vm_ip = result[1]['vm_ip']
        vm_mgr_port = result[1]['vmm_port']
	self.assertTrue(result[0])

    def test_vm_mgr_running(self):
        response = requests.get("http://" + vm_ip + ":" + vm_mgr_port + "/api/1.0/test-lab")
        print response
        self.assertEqual(response.status_code, 200)



if __name__ == "__main__":
    unittest.main()
