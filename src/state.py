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

    def __init__(self):
        self.db = pymongo.MongoClient().ovpl

    def save(self, record):
        try:
            lab_id = record["lab_spec"]["lab_id"]
            # logger.debug("Insert the record = %s" % record)
            logger.debug("lab id = %s" % lab_id)
            """Writes the information about the deployed lab to the database"""
            """ First check if the lab is deployed already"""
            records = list(self.db.ovpl.find())
            for record in records:
                if record['lab_spec']['lab_id'] == lab_id:
                    raise DuplicateRecord(lab_id)
                if "ovpl" in self.db.collection_names():
                    self.db.ovpl.insert(record)
        except Exception, e:
            raise Exception("State, save record to database failed, error = %s"
                            % str(e))

    def get_record(self, lab_id):
        records = list(self.db.ovpl.find())
        #  For now perusing the lists to get the record,
        # but, mongodb query should be executed to fectch the record.
        for record in records:
            if record['lab_spec']['lab_id'] == lab_id:
                return record

if __name__ == '__main__':
    state = State.Instance()
#    record =
