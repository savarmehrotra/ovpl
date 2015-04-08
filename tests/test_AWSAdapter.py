import unittest
import json
import os

from src.adapters.AWSAdapter import AWSAdapter


class TestAWSAdapter(unittest.TestCase):
    def setUp(self):
        # hardcoded paths are not flexible. this will only work if I run it from
        # the top-level of ovpl directory..
        self.lab_spec = json.loads(open("scripts/labspec.json").read())
        self.adapter = AWSAdapter()

    def test_create_vm(self):
        vm_id = self.adapter.create_vm(self.lab_spec)
        vm_ip = self.adapter.get_vm_ip(vm_id)

        if os.system("ping -c 1 " + vm_ip) == 0:
            print "VM successfully created"

        # TODO: testcases should have some assert statement. check python unit
        # testing

if __name__ == "__main__":
    unittest.main()
