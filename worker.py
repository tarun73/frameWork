#we need to listen on a particular channel and do work
import config, constants as C
import rabbitmqDb
import argparse, json
from subprocess import check_output
import mongoDb


def updateAccuracyInDatabase(accuracy, modelObj, expObj, modelName, experimentName, modelCollection, experimentCollection,datasetName=None):
    #check the accuracy in model and change if high
    # add the accuracy to experimentcollection
    if datasetName is not None:
        if modelObj["bestAccuracy"] < accuracy:
            modelCollection.update({"_id":modelName},
                {
                    "$set":{
                        "bestAccuracy":accuracy,
                        "bestExperimentName":experimentName,
                        "trainingset":datasetName
                    }
            })
    else:
        if modelObj["bestAccuracy"] < accuracy:
            modelCollection.update({"_id":modelName},
                {
                    "$set":{
                        "bestAccuracy":accuracy,
                        "bestExperimentName":experimentName,
                    }
            })
    return

def handleCompletion(ch,method):
    ch.basic_ack(delivery_tag=method.delivery_tag)

def handleFailure(ch,method):
    ch.basic_ack(delivery_tag=method.delivery_tag)


def doTraining(ch, method, properties, body):
    dataFromQueue = json.loads(body)
    try:
        modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                           config.get(config.PORT),
                                                           config.get(config.DATABASENAME),
                                                           config.get(config.MODELCOLLECTION))
        experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                           config.get(config.PORT),
                                                           config.get(config.DATABASENAME),
                                                           config.get(config.EXPERIMENTCOLLECTION))
        datasetCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                           config.get(config.PORT),
                                                           config.get(config.DATABASENAME),
                                                           config.get(config.DATASETCOLLECTION))
        modelName = dataFromQueue['modelName']
        modelObj = modelCollection.find_one({"_id":modelName})
        experimentName = dataFromQueue['experimentName']
        expObj = experimentCollection.find_one({"modelName":modelName,
                                                "experimentName":experimentName})
        learningRate = str(expObj['learningRate'])
        steps = str(expObj["numOfSteps"])
        layers = str(expObj["numOfLayers"])
        datasetName = None
        if "datasetName" in dataFromQueue.keys() and dataFromQueue["datasetName"] is not None:
            datasetName = dataFromQueue["datasetName"]
            datasetObj = datasetCollection.find_one({"modelName":modelName,"datasetName":dataFromQueue["datasetName"]})
            trainingImagesPath = datasetObj["trainingImagesPath"]
        else:
            trainingImagesPath = str(modelObj["trainingImagesPath"])
        output = check_output(
            ['python', 'train.py', '--i', learningRate, '--j', layers, '--k', steps, '--images', trainingImagesPath])
        accuracy = output.split(',')[4][13:-2]
        updateAccuracyInDatabase(accuracy, modelObj, expObj, modelName, experimentName, modelCollection, experimentCollection, datasetName)

        print("updated experiment ", experimentName)
        if "datasetName" in dataFromQueue.keys() and dataFromQueue["datasetName"] is not None:
            # here we can save new experiments accuracy in  array and
            experimentCollection.update({"modelName":modelName,
                                        "experimentName":experimentName},{
                                            "$pull":{
                                                "accuracies":{
                                                        "datasetName" : dataFromQueue["datasetName"]
                                                }
                                            }
                                        })
            experimentCollection.update({"modelName":modelName,
                                        "experimentName":experimentName},{
                                            "$push":{
                                                "accuracies":{
                                                    "datasetName":dataFromQueue["datasetName"],
                                                    "status":2,
                                                    "accuracy":accuracy
                                                }
                                            }
                                        })
        else:
            experimentCollection.update({"modelName":modelName,
                                        "experimentName":experimentName},{
                                            "$set":{
                                                "status":2,
                                                "accuracy": float(accuracy)
                                            }
                                        })
        handleCompletion(ch,method)
    except:
        handleFailure(ch,method)
        pass
    print("completed experiment")
    return

def consumeQueue():
    rabbitmqChannel = rabbitmqDb.getRabbitmqConsumeChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    rabbitmqChannel.basic_consume(doTraining,queue=C.TRAINING_QUEUE_NAME)
    rabbitmqChannel.start_consuming()
    return

if __name__ == '__main__':
    print('Starting worker process')
    consumeQueue()