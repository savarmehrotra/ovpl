import unittest
import json
import os

from src.adapters.AWSAdapter import AWSAdapter


class TestAWSAdapter(unittest.TestCase):
    def setUp(self):
        self.lab_spec = json.loads(open("./ovpl/scripts/labspec.json").read())
        self.adapter = AWSAdapter()          

    def test_create_vm(self):
        vm_id = self.adapter.create_vm(self.lab_spec)
        vm_ip = self.adapter.get_vm_ip(vm_id)

        if os.system("ping -c 1 " + vm_ip) == 0:
            print "VM successfully created"

if __name__ == "__main__" :
    unittest.main()

 
