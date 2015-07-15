from __init__ import *
import unittest
import requests
import time
from adapters.centos_openvz_adapter import CentOSVZAdapter
from lab_manager import LabManager
from utils.execute_commands import execute_command
from utils.git_commands import GitCommands
from httplogging.http_logger import test_logger



class TestCentOSVZAdapter(unittest.TestCase):
    base_ip = "10.2.56.230"
    lab_spec = ""
    vm_id = ""
    lab_repo_name = ""

    def setUp(self):
        self.git = GitCommands()
        self.lab = LabManager()
        lab_src_url = "https://github.com/Virtual-Labs/computer-programming-iiith.git"
        self.lab_spec = self.lab.get_lab_reqs(lab_src_url)
        self.lab_repo_name = self.git.construct_repo_name(lab_src_url)
        self.adapter = CentOSVZAdapter()
        test_logger.debug("setUp(): lab_src_url = %s, lab_repo_name = %s" %
                          (lab_src_url, self.lab_repo_name))

    def tearDown(self):
        test_logger.debug("tearDown(), vm_id = %s" % str(self.vm_id))
        self.adapter.destroy_vm(self.vm_id)

    def test_create_vm(self):
        test_logger.debug("test_create_vm()")
        (status, self.vm_id) = self.adapter.create_vm(self.lab_spec)
        test_logger.debug("test_create_vm(): status = %s, vm_id = %s" %
                          (str(status), str(self.vm_id)))
        check_cmd = "ssh root@%s 'vzlist %s'" % (self.base_ip, self.vm_id)
        test_logger.debug("test_create_vm(): check_cmd = %s" % check_cmd)
        (return_code, output) = execute_command(check_cmd)
        test_logger.debug("test_create_vm(): return_code = %s" %
                          str(return_code))
        self.assertEqual(return_code, 0)
        test_logger.debug("test_create_vm(): Test passed")

    def test_init_vm(self):
        test_logger.debug("test_create_vm()")
        (status, self.vm_id) = self.adapter.create_vm(self.lab_spec)
        test_logger.debug("test_init_vm(): vm_id = %s" % str(self.vm_id))
        (status, result) = self.adapter.init_vm(self.vm_id, self.lab_repo_name)
        test_logger.debug("test_init_vm(): status = %s" % status)
        self.assertTrue(status)
        test_logger.debug("test_init_vm(): Test passed")

    def test_vm_mgr_running(self):
        (status, self.vm_id) = self.adapter.create_vm(self.lab_spec)
        (status, result) = self.adapter.init_vm(self.vm_id, self.lab_repo_name)
        vm_ip = result['vm_ip']
        vm_port = result['vm_port']
        url = "http://%s:%s/api/1.0/test-lab" % (vm_ip, str(vm_port))
        test_logger.debug("VMMgr URL: %s" % url)

        for i in (1, 2, 4, 8, 16):
            time.sleep(i)
            try:
                response = requests.get(url)
                test_logger.debug("response = %s for ith time = %d" %
                                  response, i)
            except Exception:
                pass
            self.assertEqual(response.status_code, 200)
            test_logger.debug("test_vm_mgr_running(): Test passed")


if __name__ == "__main__":
    unittest.main()
