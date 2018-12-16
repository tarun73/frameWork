import config
import os, json
import pika
import constants as C
from random import randint
from subprocess import check_output



def publishInQueue(ObjToPublish,channel,routingKey,delivery_mode):
    status = channel.basic_publish(exchange='',
                                  routing_key=routingKey,
                                  body=json.dumps(ObjToPublish),
                                  properties=pika.BasicProperties(
                                      delivery_mode=delivery_mode,  # make message persistent
                                  ))
    return status

def makeQueueObject(modelName,experimentName):
    return {"modelName":modelName,"experimentName":experimentName}

def trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel):
    try:
        queueObj = makeQueueObject(modelName,experimentName)
        status = publishInQueue(queueObj, pikapublishChannel, C.TRAINING_QUEUE_NAME, delivery_mode=2)
        experimentCollection.update({"modelName":modelName,
                                     "experimentName":experimentName,
                                     },
                                    {
                                       "$set":{
                                        "status": 1
                                       }
                                    })
        result = {'status': 'ok', 'message': 'training for exp started'}
    except Exception as e:
        result = {'status': 'ERROR', 'message': e}
    return result

def createDefaultExperiments(modelName,modelCollection,experimentCollection):
    learningRates = [0.001,0.01,0.1]
    layers = [1,2,4]
    steps = [1000, 2000, 4000]
    expNum=1
    for learningRate in learningRates:
        for numOfLayers in layers:
            for numOfSteps in steps:
                experimentName = 'default_'+str(expNum)
                createExperiment(modelName, experimentName,learningRate,
                                numOfLayers,numOfSteps,modelCollection,experimentCollection)
                expNum+=1
    return

def createModel(modelName, modelCollection, experimentCollection):
    objectToInsert = {'_id':modelName,
                      'experiments':[],
                      'trainingImagesPath':config.get(config.TRAININGIMAGESPATH)+str(modelName)+'/',
                      'numberOfTrainingImages':0,
                      'bestAccuracy':0,
                      'bestExperimentName':None
                      }
    try:
        modelCollection.insert_one(objectToInsert)
        createDefaultExperiments(modelName,modelCollection,experimentCollection)
        return {'status': 'ok', 'message': 'Model Created'}
    except Exception as e:
        return {'status': 'ERROR', 'message': 'Model with same name already exists'}

def insertTrainingImages(modelName,imageUrls,modelCollection):
    #check if the model exists,
    try:
        obj = modelCollection.find_one({"_id":modelName})

        return {'status': 'ok', 'message': 'Images added For training'}
    except Exception as e:
        print(e)
        return {'status':'ERROR', 'message':e}

def insertTrainingImage(modelName,image,modelCollection):
    """
    :param modelName:
    :param image:
    :param modelCollection:
    :return:
    """
    #check if model exists
    try:
        obj = modelCollection.find_one({"_id":modelName})
        trainingImagesPath = obj['trainingImagesPath']
        numOfTrainingImages = obj['numberOfTrainingImages']
        if not os.path.isdir(trainingImagesPath):
            os.mkdir(trainingImagesPath)
        image.save(trainingImagesPath+str(numOfTrainingImages+1)+'.jpg')
        modelCollection.update_one({'_id': modelName}, {
            '$inc': {
                'numberOfTrainingImages': 1
            }}, upsert=False)
        return {'status': 'ok', 'message': 'Images added For training'}
    except Exception as e:
        print(e)
        return {'status': 'ERROR', 'message': e}

def createExperiment(modelName, experimentName,learningRate,numOfLayers,numOfSteps,modelCollection,experimentCollection):
    """

    :param modelName:
    :param learningRate:
    :param numOfLayers:
    :param numOfSteps:
    :param modelCollection:
    :param experimentCollection:
    :return:
    """
    try:
        #check if experiment with same name exists
        objTOCheck = {"experimentName":experimentName,"modelName":modelName}
        if experimentCollection.find_one(objTOCheck) is not None:
            return {'status': 'ERROR', 'message': 'experiment with same name aready exists'}
        else:
            obj = modelCollection.find_one({"_id": modelName})
            if obj is not None:
                expObj = {
                    'experimentName': experimentName,
                    'learningRate': float(learningRate),
                    'numOfSteps': int(numOfSteps),
                    'numOfLayers': int(numOfLayers),
                    'modelName': modelName,
                    'accuracy': 0,
                    'status': 0
                }
                insertedObjId = experimentCollection.insert_one(expObj)
                return {'status': 'ok', 'message': 'New experiment Added'}
            else:
                return {'status': 'ok', 'message': 'No Model Found'}
    except Exception as e:
        print(e)
        return {'status': 'ERROR', 'message': e}

def runDefaultExperiments(modelName,modelCollection,experimentCollection,pikapublishChannel):
    for i in range (1,28):
        experimentName = 'default_'+str(i)
        trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel)
    return {"status": "Ok", 'message': "training started on 27 experiments" }

def runTest(modelName,image,modelCollection,experimentCollection):

    """
    :param modelName:
    :param experimentName:
    :param image:
    :return:
    """
    modelObj = modelCollection.find_one({"_id":modelName})
    bestexperimentName = modelObj['bestExperimentName']
    if bestexperimentName is not None:
        expObj = experimentCollection.find_one({"modelName":modelName,
                                                "experimentName":bestexperimentName})
        name = str(randint(1000000, 9999999))
        testImagesPath =config.get(config.TESTIMAGESPATH)+str(modelName)
        if not os.path.isdir(testImagesPath):
            os.mkdir(testImagesPath)
        imagePath = testImagesPath+'/'+name+'.jpg'
        image.save(imagePath)
        learningRate = str(expObj['learningRate'])
        steps = str(expObj["numOfSteps"])
        layers = str(expObj["numOfLayers"])
        output = check_output(
            ['python', 'test.py', '--i', learningRate, '--j', layers, '--k', steps, '--image', imagePath])
        accuracy = output.split(',')[4][13:-2]
        return {"Status": "ok","body":{"accuracy":accuracy, "learningRate": learningRate, "steps": steps,"layers":layers,
                "Experiment":bestexperimentName}}
    else:
        return {"Status":"ok","body":{"Experiment":bestexperimentName}}

def getAllAccuracies(modelName, experimentCollection, modelCollection,bestAccuracyFlag=False):
    finalObj = {
        "bestaccuracy":0,
        "bestExperimentName":None,
    }
    modelObj = modelCollection.find_one({
        "_id": modelName
    })
    finalObj["bestExperimentName"] = modelObj["bestExperimentName"]
    finalObj["bestaccuracy"] = modelObj["bestAccuracy"]
    if not bestAccuracyFlag:
        finalObj["AllExperiments"] = []
        experimentObjList = experimentCollection.find({
            "modelName":modelName
        })
        for expObj in experimentObjList:
            smallObj = {}
            smallObj["experimentName"]= expObj["experimentName"]
            smallObj["layers"]= expObj["numOfLayers"]
            smallObj["steps"]= expObj["numOfSteps"]
            smallObj["learningRate"]= expObj["learningRate"]
            if "status" in expObj.keys() and expObj["status"] == 2:
                smallObj["accuracy"]= expObj["accuracy"]
            finalObj["AllExperiments"].append(smallObj)
    return finalObj
