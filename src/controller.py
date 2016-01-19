"""
Main interface of OVPL with the external world.
Controller interfaces with LabManager and VMPoolManager.

"""


from datetime import datetime
from __init__ import *
from lab_manager import LabManager
from vm_pool_manager import VMPoolManager
from state import State
from state import Record
from httplogging.http_logger import logger
from utils.git_commands import GitCommands
from utils.execute_commands import execute_command


class Controller:
    state = None
    lab_spec = None
    lab_deployment_record = None
    labmgr = None
    vmpoolmgr = None
    git = None
    deploy_recod = None

    def __init__(self):
        self.state = State.Instance()
        self.lab_spec = {}
        self.labmgr = LabManager()
        self.vmpoolmgr = VMPoolManager()
        self.git = GitCommands()
        self.deploy_record = Record()

    def test_lab(self, current_user, lab_id, lab_src_url, revision_tag=None):
        logger.debug("test_lab() for lab ID %s, git url %s, current user %s"
                     % (lab_id, lab_src_url, current_user))
        try:
            '''
            record_list = self.state.read_record(lab_src_url)
            if record_list:
                msg = "Lab with the url = %s is already deployed" % lab_src_url
                logger.debug(msg)
                return msg
            '''
            # Get lab sources and from it the deployment specification
            # of the lab
            self.lab_spec = self.labmgr.get_lab_reqs(lab_src_url,
                                                     revision_tag)
            self.update_lab_spec(lab_id, lab_src_url, revision_tag)

            # create a VM to deploy the lab
            logger.debug("test_lab(); invoking create_vm() on vmpoolmgr")
            self.deploy_record.record = self.vmpoolmgr.create_vm(self.lab_spec)

            logger.debug("test_lab(): Returned from VMPool = %s" %
                         (str(self.deploy_record.record)))
            ip = self.deploy_record.record['vm_info']['vm_ip']
            port = self.deploy_record.record['vm_info']['vm_port']
            vmmgrurl = "http://" + ip
            lab_id = self.deploy_record.record['lab_spec']['lab_id']
            logger.debug("test_lab(): vmmgrurl = %s" % (vmmgrurl))

            # deploy the lab on the newly created container.
            try:
                (ret_val, ret_str) = self.labmgr.test_lab(vmmgrurl,
                                                          port,
                                                          lab_src_url,
                                                          revision_tag)
                if(ret_val):
                    self.update_deploy_record(current_user)
                    self.state.save(self.deploy_record.record)
                    logger.info("test_lab(): test succcessful, ip = %s" % ip)
                    domain_name = self.register_lab(lab_id, ip)
                    return domain_name
                else:
                    logger.error("test_lab(); Test failed with error:" +
                                 str(ret_str))
                    return "Test failed: See log file for errors"
            except Exception, e:
                logger.error("test_lab(); Test failed with error: %s" % str(e))
                return "Test failed: See log file for errors"
        except Exception, e:
            logger.error("test_lab(): Test failed with error: %s" % str(e))
            return "Test failed: See log file for errors"

    def update_lab_spec(self, lab_id, lab_src_url, revision_tag):
        self.lab_spec['lab']['description']['id'] = \
            self.lab_spec['lab_id'] = lab_id
        self.lab_spec['lab']['lab_src_url'] = lab_src_url
        self.lab_spec['lab']['lab_repo_name'] = \
            self.git.construct_repo_name(lab_src_url)
        self.lab_spec['lab']['revision_tag'] = revision_tag
        self.lab_spec['lab']['runtime_requirements']['hosting'] = 'dedicated'
        logger.debug("lab_repo_name: %s" %
                     (self.lab_spec['lab']['lab_repo_name']))

    def update_deploy_record(self, current_user):
        logger.debug("current user is %s" % current_user)
        self.deploy_record.record['lab_history']['deployed_by'] = current_user
        self.deploy_record.record['lab_history']['released_by'] = 'dummy'
        self.deploy_record.record['lab_history']['released_on'] = \
            datetime.utcnow()
        # This is a hack, just to avoid duplicate records.
        self.deploy_record.record['id'] = \
            self.lab_spec['lab']['lab_src_url'] + str(datetime.utcnow())
        logger.debug("Lab deployed by %s" %
                     self.deploy_record.record['lab_history']['deployed_by'])

    def undeploy_lab(self, lab_id):
        logger.debug("undeploy_lab for lab_id %s" % lab_id)
        self.vmpoolmgr.undeploy_lab(lab_id)
        return "Success"

    def register_lab(self, lab_id, ip_address):
        ansible_url = "ssh root@ansible.base4.vlabs.ac.in"
        service_name = "hosting_service"
        service_action = "register"
        command = (r'"%s %s %s %s %s"' %
                   (ansible_url, service_name, service_action, lab_id, ip_address ))
        logger.debug("Hook's service command =  %s" %
                     command)
        (ret_code, output) = execute_command(command)
        if ret_code == 0:
            return lab_id + "base4.vlabs.ac.in"

if __name__ == '__main__':

    def test_ctrl_test_lab():
        lab_src_url = \
            "https://github.com/Virtual-Labs/computer-programming-iiith.git"
        c = Controller()
        print c.test_lab("travula@gmail.com", "cse02", lab_src_url)

    def test_labmgr_test_lab():
        vmmgrurl = "http://172.16.0.2"
        lab_src_url = \
            "https://github.com/Virtual-Labs/computer-programming-iiith.git"
        port = "9089"
        revision_tag = None
        labmgr = LabManager()
        try:
            (ret_val, ret_str) = labmgr.test_lab(vmmgrurl,
                                                 port,
                                                 lab_src_url,
                                                 revision_tag)
        except Exception, e:
            logger.error("test_lab(); Test failed with error: " + str(e))

    """ List the tests here to be run """
    # test_ctrl_test_lab()
