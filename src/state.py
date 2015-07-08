import pymongo
from __init__ import *
from singleton import Singleton
from httplogging.http_logger import logger


class Record:
    def __init__(self):
        self.record = {
            "lab_spec": None,
            "vm_info": {
                "vm_id": None,
                "vm_ip": None,
                "vm_port": None
            },
            "vmpool_info": {
                "vmpool_id": None,
                "vm_description": None,
                "adapter_ip": None,
                "adapter_port": None
            },
            "vm_status": {
                "last_known_status": None,
                "last_successful_connection": None,
                "reconnect_attempts": None,
                "disk_usage": None,
                "mem_usage": None
            },
            "lab_history": {
                "released_by": None,
                "released_on": None,
                "destroyed_by": None,
                "destroyed_on": None
            }
        }


class DuplicateRecord(Exception):
    def __init__(self, lab_id):
        self.lab_id = lab_id

    def __str__(self):
        return repr("Duplicate record found in the database with lab id = %s"
                    % self.lab_id)


@Singleton
class State:
    db = None
    collection_name = None

    def __init__(self):
        self.db = pymongo.MongoClient().ovpl
        self.collection_name = "deploy_records"

    def save(self, record):
        try:
            record_id = record["id"]
            # logger.debug("Insert the record = %s" % record)
            logger.debug("record id = %s" % record_id)
            """Writes the information about the deployed lab to the database"""
            """ First check if the lab is deployed already"""
            existing_record = self.read_record(record_id)
            if not existing_record:
                self.write_record(record)
                logger.debug("Insert of record with Id = %s successful" %
                             record_id)
            else:
                raise DuplicateRecord(record_id)
        except Exception, e:
            raise Exception("State, save record to database failed, error = %s" % str(e))

    def read_record(self, id):
        return list(self.db[self.collection_name].find({'id': id}))

    def read_records(self):
        return list(self.db[self.collection_name].find())

    def write_record(self, record):
        self.db[self.collection_name].insert(record)

    def delete_record(self, id):
        return list(self.db[self.collection_name].remove({'id': id}))

    def delete_records(self):
        return list(self.db[self.collection_name].remove())

if __name__ == '__main__':
    from vm_pool import VMPool
    from controller import Controller

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

    def test_record(lab_src_url=None):
        lab_src_url = \
            "https://github.com/Virtual-Labs/computer-programming-iiith.git"
        deploy_record = create_record(lab_src_url)
        if deploy_record.record['id'] == lab_src_url:
            logger.debug("Test: test_record PASSED")

    def test_save():
        lab_src_url = \
            "http://github.com/Virtual-Labs/computer-programming-iiith.git"
        state = State.Instance()
        deploy_record = create_record(lab_src_url)
        state.save(deploy_record.record)

    # Run Tests
    # test_record()
    try:
        test_save()
    except Exception, e:
        logger.debug(str(e))
