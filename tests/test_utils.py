from __init__ import *
from controller import Controller
from vm_pool import VMPool
from httplogging.http_logger import logger


def create_record(lab_src_url=None, c=None):
    logger.debug("Test case insert_record")
    if c is None:
        c = Controller()
        if lab_src_url is None:
            lab_src_url = \
                "https://github.com/Virtual-Labs/computer-programming-iiith.git"
    revision_tag = None
    lab_id = "cse04"
    current_user = "travula@gmail.com"
    vmpool_id = 1
    vm_description = "LINUXAdapter"
    adapter_ip = "http://localhost"
    adapter_port = "8000"
    create_path = "/api/1.0/vm/create"
    destroy_path = "/api/1.0/vm/destroy"
    vm_id = "123"
    vm_ip = "10.12.13.114"
    vm_port = "8089"
    try:
        vm_pool = VMPool(vmpool_id, vm_description, adapter_ip,
                         adapter_port, create_path, destroy_path)
        c.lab_spec = c.labmgr.get_lab_reqs(lab_src_url, revision_tag)
        logger.debug("returned from lab_manager and the controller's lab_spec = %s"
                     % c.lab_spec)
        c.update_lab_spec(lab_id, lab_src_url, revision_tag)
        record = vm_pool.construct_state(c.lab_spec, vm_id,
                                         vm_ip, vm_port)
        c.deploy_record.record = record
        c.update_deploy_record(current_user)
        logger.debug("deploy_record = %s" % c.deploy_record.record)
        logger.debug("ID = %s" % c.deploy_record.record['id'])
        return c.deploy_record
    except Exception, e:
        logger.debug("Error inserting record, error is %s" % str(e))

if __name__ == '__main__':
    print create_record().record['id']
