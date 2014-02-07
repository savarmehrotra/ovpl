import pymongo
from Singleton import Singleton

@Singleton
class State:
    def __init__(self):
        self.db = pymongo.MongoClient().ovpl
        self.restore()

    def restore(self):
        """Restores state from a mongodb collection."""
        if "ovpl" in self.db.collection_names():
            self.state = list(self.db.ovpl.find())
        else:
            self.state = []

    def save(self):
        """Writes the current state to mongodb(disk)"""
        if "ovpl" in self.db.collection_names():
            self.db.ovpl.rename("ovpl-last", dropTarget=True)
        if bool(self.state):
            self.db.ovpl.insert(self.state)