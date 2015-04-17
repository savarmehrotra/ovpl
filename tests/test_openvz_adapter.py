import unittest
import json
import requests
import os
from src.adapters.CentOSVZAdapter import CentOSVZAdapter, get_vm_ip
from src.LabManager import get_lab_reqs
vm_id = ''
vm_ip = ''
vmm_port = ''

lab_repo_name = 'computer-programming-iiith'
class TestCentOSVZAdapter(unittest.TestCase):
    def setUp(self):
	    self.lab_spec = json.loads(open("scripts/labspec.json").read())
	    self.adapter = CentOSVZAdapter()

    def test_create_vm(self):
	    global vm_id
	    (status, vm_id) = self.adapter.create_vm(self.lab_spec)
	    #print vm_id
	    vm_ip = get_vm_ip(vm_id)
	    #print vm_ip
	    response = os.system("ping -c 1 " + vm_ip)
	    self.assertEqual(response, 0)

    def test_init_vm(self):
	    global vm_id
	    global lab_repo_name
	    global vm_ip
	    (status, result) = self.adapter.init_vm(vm_id, lab_repo_name)
	    print result
	    print status
	    vm_ip = result['vm_ip']
	    print vm_ip
	    vmm_port = result['vmm_port']
	    print vmm_port
	    self.assertTrue(status)

    def test_vm_mgr_running(self):
	    response = self.adapter.start_vm_manager(vm_id)
	    print response
	    self.assertTrue(response)


if __name__ == "__main__":
    unittest.main()
