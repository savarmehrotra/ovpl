import unittest
import json
import requests

from src.adapters.AWSAdapter import AWSAdapter
from src.LabManager import get_lab_reqs


class TestAWSAdapter(unittest.TestCase):
    def setUp(self):
        # hardcoded paths are not flexible. this will only work if I run it from
        # the top-level of ovpl directory..
        self.lab_spec = json.loads(open("scripts/labspec.json").read())
        self.adapter = AWSAdapter()
	self.repo_name = "ovpl"
        get_lab_reqs("https://github.com/vlead/ovpl.git")
        result = self.adapter.create_vm(self.lab_spec)
        self.vm_id = result[1]
#       print self.vm_id 

    def setup_test_vm_mgr_running(self):
#       print 'inside setup for test_vm_mgr_running'
        result = self.adapter.init_vm(self.vm_id, self.repo_name)
        return result

    def tearDown(self):
#       print "tearing down" + self.vm_id
        self.adapter.destroy_vm(self.vm_id)        

    def test_create_vm(self):
        vm_ip = self.adapter.get_vm_ip(self.vm_id)
        instance = self.adapter.get_instance(self.vm_id)
       # print vm_ip
       # print self.vm_id
	# after an instance is created, it should be in one of the following states:
        # 0: instance creation pending, 16: instance running
        self.assertIn(instance.state_code, (0, 16))

    def test_init_vm(self):
#       print 'in init_vm'
        result = self.setup_test_vm_mgr_running()
#        print result
        self.assertTrue(result[0])

    def test_vm_mgr_running(self):
#       print 'in third test case'
        result = self.setup_test_vm_mgr_running()
        vm_ip = result[1]['vm_ip']
        vm_mgr_port = result[1]['vmm_port']
#       print vm_ip
#       print vm_mgr_port
        vm_mgr_url = "http://{0}:{1}/api/1.0/test-lab".format(vm_ip, vm_mgr_port)
        response = requests.get(vm_mgr_url)
#       print response
        self.assertEqual(response.status_code, 200)



if __name__ == "__main__":
    unittest.main()
