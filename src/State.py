import pymongo
from src.singleton import Singleton


@Singleton
class State:
    __state = []

    def __init__(self):
        self.db = pymongo.MongoClient().ovpl
        self.restore()

    def restore(self):
        """Restores state from a mongodb collection."""
        if "ovpl" in self.db.collection_names():
            self.__state = list(self.db.ovpl.find())
        else:
            self.__state = []

    def save(self):
        """Writes the current state to mongodb(disk)"""
        if "ovpl" in self.db.collection_names():
            self.db.ovpl.rename("ovpl-last", dropTarget=True)
        if bool(self.__state):
            self.db.ovpl.insert(self.__state)
