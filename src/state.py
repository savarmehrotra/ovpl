import pymongo
from __init__ import *
from singleton import Singleton
from httplogging.http_logger import logger


class DuplicateRecord(Exception):
    def __init__(self, lab_id):
        self.lab_id = lab_id

    def __str__(self):
        return repr(self.lab_id)


@Singleton
class State:
    db = None

    def __init__(self):
        self.db = pymongo.MongoClient().ovpl

    def save(self, record):
        logger.debug("Insert the record = %s" % record)
        """Writes the information about the deployed lab to the database"""
        """ First check if the lab is deployed already"""
        records = list(self.db.ovpl.find())
        for record in records:
            if record['lab_spec']['lab_id'] == lab_id:
                raise DuplicateRecord(lab_id)
        if "ovpl" in self.db.collection_names():
            self.db.ovpl.insert(record)

    def get_record(self, lab_id):
        records = list(self.db.ovpl.find())
        #  For now perusing the lists to get the record,
        # but, mongodb query should be executed to fectch the record.
        for record in records:
            if record['lab_spec']['lab_id'] == lab_id:
                return record
