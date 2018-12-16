#we need to listen on a particular channel and do work
import config, constants as C
import rabbitmqDb
import argparse, json
from subprocess import check_output
import mongoDb


def updateAccuracyInDatabase(accuracy, modelObj, expObj, modelName, experimentName, modelCollection, experimentCollection):
    #check the accuracy in model and change if high
    # add the accuracy to experimentcollection
    expId = experimentCollection.update({
        "experimentName":experimentName,
        "modelName":modelName,
        },{
            "$set":{
                "accuracy":float(accuracy)
            }
    })
    if modelObj["bestAccuracy"] < accuracy:
        modelCollection.update({"_id":modelName},
            {
                "$set":{
                    "bestAccuracy":accuracy,
                    "bestExperimentName":experimentName
                }
        })
    return

def handleCompletion(ch,method):
    ch.basic_ack(delivery_tag=method.delivery_tag)

def doTraining(ch, method, properties, body):
    dataFromQueue = json.loads(body)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    modelName = dataFromQueue['modelName']
    modelObj = modelCollection.find_one({"_id":modelName})
    experimentName = dataFromQueue['experimentName']
    expObj = experimentCollection.find_one({"modelName":modelName,
                                            "experimentName":experimentName})
    learningRate = str(expObj['learningRate'])
    steps = str(expObj["numOfSteps"])
    layers = str(expObj["numOfLayers"])
    trainingImagesPath = str(modelObj["trainingImagesPath"])
    output = check_output(
        ['python', 'train.py', '--i', learningRate, '--j', layers, '--k', steps, '--images', trainingImagesPath])
    #"{'i': '0.001', 'images': '/home/ubuntu/TrainingImages/', 'k': '2', 'j': '2', 'accuracy': 0.3420194533724594}\n"
    accuracy = output.split(',')[4][13:-2]
    updateAccuracyInDatabase(accuracy, modelObj, expObj, modelName, experimentName, modelCollection, experimentCollection)
    print("updated experiment ", experimentName)
    experimentCollection.update({"modelName":modelName,
                                "experimentName":experimentName},{
                                    "$set":{
                                        "status":2
                                    }
                                })
    handleCompletion(ch,method)
    print("completed experiment")
    return

def consumeQueue(type, prefetch=1):
    rabbitmqChannel = rabbitmqDb.getRabbitmqConsumeChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    rabbitmqChannel.basic_consume(doTraining,queue=C.TRAINING_QUEUE_NAME)
    rabbitmqChannel.start_consuming()
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Worker')
    parser.add_argument('-t', '--type', help='Type of processing',
                        default=0)
    args = vars(parser.parse_args())
    workerType = int(args['type'])
    print('Starting worker process of type: '+str(workerType))
    consumeQueue(workerType)