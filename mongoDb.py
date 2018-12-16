from pymongo import MongoClient

mongo_object = None
collection_object = {}

def getMongoClient(host,port):
    global mongo_object
    if mongo_object is None:
        mongo_object = MongoClient(host,port)
    return mongo_object


def getMongoCollectionClient(host,port,dbName,collectionName):
    global mongo_object
    global collection_object
    if collectionName not in collection_object or collection_object[collectionName] is None:
        if mongo_object is None:
            mongo_object = getMongoClient(host,port)
        collection_object[collectionName] = mongo_object[dbName][collectionName]
    return collection_object[collectionName]

