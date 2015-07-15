# Standard Library imports
import unittest
import json
import requests
from __init__ import *

# ADS imports
from adapters.aws_adapter import AWSAdapter
from lab_manager import LabManager
from httplogging.http_logger import test_logger


class TestAWSAdapter(unittest.TestCase):
    # common setup for all test cases
    def setUp(self):
        # hardcoded paths are not flexible. this will only work if I run it from
        # the top-level of ovpl directory..
        self.lab_spec = json.loads(open("scripts/labspec.json").read())

        self.adapter = AWSAdapter()
        self.lab = LabManager()
        
        # the source code of the lab to be tested for deployment is copied
        # in /root/labs folder. here, ovpl is itself treated as a lab.
        self.repo_name = "ovpl"
        self.lab.get_lab_reqs("https://github.com/vlead/ovpl.git")

        # VM creation is part of setup since this is the requirement for every
        # test case.
        result = self.adapter.create_vm(self.lab_spec)
        self.vm_id = result[1]
        test_logger.debug("setup(): vm_id = %s" % self.vm_id)

    # set up for testing VMManager service running
    def setup_test_vm_mgr_running(self):
        #  two test cases are dependent on running init_vm() and since
        #  tearDown() happens after every test case, this ensures
        #  that init_vm() is available when required.
        test_logger.debug("inside setup for test_vm_mgr_running()")

        result = self.adapter.init_vm(self.vm_id, self.repo_name)
        return result

    def tearDown(self):
        test_logger.debug("tearDown(): destroying vm : %s" % self.vm_id)
        self.adapter.destroy_vm(self.vm_id)

    def test_create_vm(self):
        vm_ip = self.adapter.get_vm_ip(self.vm_id)
        instance = self.adapter.get_instance(self.vm_id)
        test_logger.debug("test_create_vm(): vm_ip : %s for new VM" % vm_ip)

        # after an instance is created, it should be in one of the following
        # states:
        # 0: instance creation pending, 16: instance running
        self.assertIn(instance.state_code, (0, 16))

    def test_init_vm(self):
        test_logger.debug("in init_vm")

        result = self.setup_test_vm_mgr_running()
        test_logger.debug("test_init_vm(): result : %s" % result[0])

        self.assertTrue(result[0])

    def test_vm_mgr_running(self):
        test_logger.debug("running third test case")
        #
        result = self.setup_test_vm_mgr_running()

        vm_ip = result[1]['vm_ip']
        test_logger.debug("test_vm_mgr_running(): vm ip : %s" % vm_ip)

        vm_mgr_port = result[1]['vm_port']
        test_logger.debug("test_vm_mgr_running(): vm manager port : %s" %
                          vm_mgr_port)

        vm_mgr_url = "http://{0}:{1}/api/1.0/test-lab".\
            format(vm_ip, vm_mgr_port)

        response = requests.get(vm_mgr_url)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
