import unittest
import json
import requests
import subprocess
from src.adapters.CentOSVZAdapter import CentOSVZAdapter, get_vm_ip
from src.LabManager import get_lab_reqs
from src.utils.execute_commands import *
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
	    print vm_id
	    vm_ip = get_vm_ip(vm_id)
	    print vm_ip
	    check_cmd = "ssh root@10.4.12.24 'vzlist " + vm_id + " | grep " + vm_id + "'"
	    #response = subprocess.call(check_cmd)
	    response = execute_command(check_cmd)
	    self.assertEqual(response[0], 0)
	    #response = subprocess.call("ping -c 1 " + vm_ip, shell=True)

    def test_init_vm(self):
	    global lab_repo_name
	    global vm_ip
	    global vmm_port
	    (status, result) = self.adapter.init_vm(vm_id, lab_repo_name)
	    print result
	    print status
	    vm_ip = result['vm_ip']
	    print vm_ip
	    vmm_port = result['vmm_port']
	    print vmm_port
	    self.assertTrue(status)

    def test_vm_mgr_running(self):
	    #print vm_ip
	    #print vmm_port
	    url = "http://" + vm_ip + ":" + vmm_port+ "/api/1.0/test-lab"
	    print url
	    response = requests.get(url)
	    print response
	    self.assertEqual(response.status_code, 200)	
    #def tearDown(self):
	    #self.adapter.destroy_vm_id)

if __name__ == "__main__":
    unittest.main()
