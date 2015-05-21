import pymongo
from src.singleton import Singleton


@Singleton
class State:
    db = None

    def __init__(self):
        self.db = pymongo.MongoClient().ovpl

    def save(self, record):
        """Writes the information about the deployed lab to the database"""
        if "ovpl" in self.db.collection_names():
            self.db.ovpl.insert(record)
