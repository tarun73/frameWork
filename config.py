import os, json

HOST='host'
PORT='port'
DATABASENAME='databaseName'
MODELCOLLECTION='modelCollectionName'
EXPERIMENTCOLLECTION='experimentCollectionName'
TRAININGIMAGESPATH='trainingImagesPath'
TESTIMAGESPATH='testImagesPath'
PIKA_HOST='pika_host'
PIKA_ID='pika_id'
PIKA_PASSWORD='pika_password'

script_dir = os.path.dirname(__file__)
configFilePathJson = os.path.join(script_dir, 'config.json')
config = {}
config = json.load(open(configFilePathJson,'r'))


def get(key):
    return config[key]
