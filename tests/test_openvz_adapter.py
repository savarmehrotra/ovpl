import unittest
import json
import requests
import os

from src.adapters.CentOSVZAdapter import CentOSVZAdapter
class TestCentOSVZAdapter(unittest.TestCase):
    def setUp(self):
        self.lab_spec = json.loads(open("scripts/labspec.json").read())
        self.adapter = CentOSVZAdapter()

    def test_create_vm(self):
        vm_id = self.adapter.create_vm(self.lab_spec)
        vm_ip = self.adapter.get_vm_ip(vm_id)
        print vm_ip
        print vm_id
        hostname = "google.com"
        response = os.system("ping -c 1 " + hostname)
        self.assertTrue(response, 0)


if __name__ == "__main__":
    unittest.main()

