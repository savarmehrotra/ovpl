import unittest
import json
import requests
import os

from src.adapters.CentOSVZAdapter import CentOSVZAdapter, get_vm_ip
vm_id = ''
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
        response = os.system("ping -c 1 " + vm_ip)
        self.assertEqual(response, 0)

    def test_init_vm(self):
        global vm_id
        global lab_repo_name
        (status, result) = self.adapter.init_vm(vm_id, lab_repo_name)
        print result
        print status
        self.assertTrue(status)


if __name__ == "__main__":
    unittest.main()
    
