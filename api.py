import config
import os, json
import pika, urllib
import constants as C
from random import randint
from subprocess import check_output

def makeTrainingData(modelName,datasetName,modelCollection,datasetCollection):
    modelObj = modelCollection.find_one({"_id":modelName})
    trainingPathold = modelObj['trainingImagesPath']
    dataObj = datasetCollection.find_one({"modelName":modelName,"datasetName":datasetName})
    trainingPath = dataObj['trainingImagesPath']
    if not os.path.isdir(trainingPathold):
        os.mkdir(trainingPathold)

    if not os.path.isdir(trainingPath):
        os.mkdir(trainingPath)

    for image in dataObj['imageNames']:
        try:
            if not os.path.exists(trainingPath+image):
                os.symlink(trainingPathold+image,trainingPath+image)
        except:
            pass
    print('done making new train set')
    return

def publishInQueue(ObjToPublish,channel,routingKey,delivery_mode):
    status = channel.basic_publish(exchange='',
                                  routing_key=routingKey,
                                  body=json.dumps(ObjToPublish),
                                  properties=pika.BasicProperties(
                                      delivery_mode=delivery_mode,  # make message persistent
                                  ))
    return status

def makeQueueObject(modelName,experimentName,datasetName):
    return {"modelName":modelName,"experimentName":experimentName,"datasetName":datasetName}

def checkIfModelExists(modelName,modelCollection):
    flag = True
    if modelCollection.find_one({"_id":modelName}) is None:
        flag = False
    return flag

def trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel,datasetCollection,datasetName=None):
    if checkIfModelExists(modelName,modelCollection):
        try:
            if datasetName is not None:
                makeTrainingData(modelName,datasetName,modelCollection,datasetCollection)
            queueObj = makeQueueObject(modelName,experimentName,datasetName)
            status = publishInQueue(queueObj, pikapublishChannel, C.TRAINING_QUEUE_NAME, delivery_mode=2)
            experimentCollection.update({"modelName":modelName,
                                         "experimentName":experimentName,
                                         },
                                        {
                                            "$push":{
                                                "accuracies": {"datasetName":datasetName,
                                                               "status":1,
                                                               "accuracy":0}
                                            },
                                           "$set":{
                                            "status": 1
                                           }
                                        })
            result = {'status': 'ok', 'message': 'training for exp started'}
        except Exception as e:
            result = {'status': 'ERROR', 'message': e}
    else:
        result = {'status': 'ERROR', 'message': 'Model doesnot exist'}
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

def insertTrainingImages(modelName,imageUrls,modelCollection,datasetCollection,datasetName=None):
    try:
        obj = modelCollection.find_one({"_id":modelName})
        trainingImagesPath = obj['trainingImagesPath']
        numOfTrainingImages = obj['numberOfTrainingImages']
        if not os.path.isdir(trainingImagesPath):
            os.mkdir(trainingImagesPath)
        for imageUrl in imageUrls:
            imageSavePath = trainingImagesPath+str(numOfTrainingImages+1)+'.jpg'
            image = urllib.URLopener()
            image.retrieve(imageUrl,imageSavePath)
            numOfTrainingImages+=1
            if datasetName is not None:
                datasetCollection.update({"datasetName": datasetName, "modelName": modelName},
                                         {"$push": {"imageNames": str(numOfTrainingImages + 1) + '.jpg'}})
        modelCollection.update({"_id":modelName},{"$set":{"numberOfTrainingImages":numOfTrainingImages}})
        return {'status': 'ok', 'message': 'Images added For training'}
    except Exception as e:
        print(e)
        return {'status':'ERROR', 'message':e}

def insertTrainingImage(modelName,image,modelCollection,datasetCollection,datasetName=None):
    """
    :param modelName:
    :param image:
    :param modelCollection:
    :return:
    """
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
        if datasetName is not None:
            datasetCollection.update({"datasetName":datasetName,"modelName":modelName},
                                     {"$push":{"imageNames":str(numOfTrainingImages+1)+'.jpg'}})
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
                    'accuracies': [],
                    'status': 0
                }
                insertedObjId = experimentCollection.insert_one(expObj)
                return {'status': 'ok', 'message': 'New experiment Added'}
            else:
                return {'status': 'ERROR', 'message': 'No Model Found'}
    except Exception as e:
        print(e)
        return {'status': 'ERROR', 'message': e}

def runDefaultExperiments(modelName,modelCollection,experimentCollection,pikapublishChannel,datasetCollection,datasetName=None):
    for i in range (1,28):
        experimentName = 'default_'+str(i)
        trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel,datasetCollection,datasetName)
    return {"status": "Ok", 'message': "training started on 27 experiments" }

def runTest(modelName,image,modelCollection,experimentCollection):

    """
    :param modelName:
    :param experimentName:
    :param image:
    :return:
    """
    if checkIfModelExists(modelName,modelCollection):
        try:
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
                result =  {"Status": "ok","body":{"accuracy":accuracy, "learningRate": learningRate, "steps": steps,"layers":layers,
                        "Experiment":bestexperimentName}}
            else:
                result = {"Status":"ERROR","message":"no experiment done yet"}
        except Exception as e:
            result = {"status" : "ERROR", "message":e}
    else:
        result = {'status': 'ERROR', 'message': 'Model doesnot exist'}
    return result

def getAllAccuracies(modelName, experimentCollection, modelCollection,experimentName=None,bestAccuracyFlag=False):
    if checkIfModelExists(modelName,modelCollection):
        if experimentName is not None:
            expObj = experimentCollection.find_one({"modelName":modelName,"experimentName":experimentName})
            if expObj is None:
                result = {"status":"ERROR","message":"no experiment with this name exists"}
            else:
                if bestAccuracyFlag :
                    finalObj = {
                        "bestaccuracy": 0,
                        "experiment": None,
                        "bestDataset": None,
                    }
                    bestAccuracy = 0
                    bestDataset = None
                    for acc in expObj['accuracies']:
                        if acc["status"] == 2:
                            if acc["accuracy"] > bestAccuracy:
                                bestAccuracy = acc["accuracy"]
                                bestDataset = acc["datasetName"]
                    finalObj["bestaccuracy"] = bestAccuracy
                    finalObj["experiment"] = experimentName
                    finalObj["bestDataset"] = bestDataset
                    result = {"status":"ok","body":finalObj}
                else:
                    #all accuracies in experiment
                    finalObj = {
                        "AllExperiments":[]
                    }
                    experimentObjList = [expObj]
                    for expObj in experimentObjList:
                        smallObj = {}
                        smallObj["accuracies"] = []
                        if len(expObj["accuracies"]) > 0:
                            for acc in expObj['accuracies']:
                                if acc["status"] == 2:
                                    smallObj["accuracies"].append({"datasetName":acc["datasetName"],"accuracy":acc["accuracy"]})
                        smallObj["experimentName"]= expObj["experimentName"]
                        smallObj["layers"]= expObj["numOfLayers"]
                        smallObj["steps"]= expObj["numOfSteps"]
                        smallObj["learningRate"]= expObj["learningRate"]
                        # if "status" in expObj.keys() and expObj["status"] == 2:
                        #     smallObj["accuracy"]= expObj["accuracy"]
                        if len(smallObj["accuracies"])>0:
                            finalObj["AllExperiments"].append(smallObj)
                    result = {"status":"ok","body":finalObj}
        else:
            finalObj = {
                "bestaccuracy":0,
                "bestExperiment":None,
                "bestDataset":None
            }
            modelObj = modelCollection.find_one({
                "_id": modelName
            })
            finalObj["bestExperiment"] = modelObj["bestExperimentName"]
            finalObj["bestaccuracy"] = modelObj["bestAccuracy"]
            if "trainingset" in modelObj.keys():
                finalObj["bestDataset"] = modelObj["trainingset"]
            if not bestAccuracyFlag:
                finalObj["AllExperiments"] = []
                experimentObjList = experimentCollection.find({
                    "modelName":modelName
                })
                for expObj in experimentObjList:
                    smallObj = {}
                    smallObj["accuracies"] = []
                    if len(expObj["accuracies"]) > 0:
                        for acc in expObj['accuracies']:
                            if acc["status"] == 2:
                                smallObj["accuracies"].append({"datasetName":acc["datasetName"],"accuracy":acc["accuracy"]})
                    smallObj["experimentName"]= expObj["experimentName"]
                    smallObj["layers"]= expObj["numOfLayers"]
                    smallObj["steps"]= expObj["numOfSteps"]
                    smallObj["learningRate"]= expObj["learningRate"]
                    # if "status" in expObj.keys() and expObj["status"] == 2:
                    #     smallObj["accuracy"]= expObj["accuracy"]
                    if len(smallObj["accuracies"])>0:
                        finalObj["AllExperiments"].append(smallObj)
            result = {"status":"ok","body" :finalObj}
    else:
        result = {'status': 'ERROR', 'message': 'Model doesnot exist'}
    return result

def getAllAccuraciesExperiments(modelName, experimentName,experimentCollection, modelCollection):
    if checkIfModelExists(modelName,modelCollection):
        finalObj = {
            "bestaccuracy":0,
            "ExperimentName":None,
        }
        experimentObjList = experimentCollection.find_one({
            "modelName": modelName,
            "experimentName": experimentName
        })
        best_accuracy =0
        datasetName = None
        for accuracy in experimentObjList["accuracies"]:
            if accuracy["accuracy"] > best_accuracy:
                best_accuracy = accuracy["accuracy"]
                datasetName = accuracy["datasetName"]
        finalObj["bestaccuracy"] = best_accuracy
        finalObj["ExperimentName"] = experimentName
        finalObj["datasetName"] = datasetName
        result = {"status":"ok","body": finalObj}
    else:
        result = {'status': 'ERROR', 'message': 'Model doesnot exist'}
    return result

def createDataset(modelName,datasetName, modelCollection, datasetCollection):

    objectToInsert = {
                      'modelName':modelName,
                      'datasetName' : datasetName,
                      'trainingImagesPath':config.get(config.DATASETIMAGESPATH)+str(modelName)+'/'+str(datasetName),
                      'numberOfTrainingImages':0,
                      'imageNames' : []
                      }
    try:
        if datasetCollection.find_one({"modelName":modelName,"datasetName":datasetName}) is not None:
            result = {'status': 'ERROR', 'message': 'dataset with same name already exists'}
        else:
            if not os.path.isdir(config.get(config.DATASETIMAGESPATH)+str(modelName)):
                os.mkdir(config.get(config.DATASETIMAGESPATH)+str(modelName))
            datasetCollection.insert_one(objectToInsert)
            result = {'status': 'ok', 'message': 'Dataset Created'}
    except Exception as e:
        result = {'status': 'ERROR', 'message': 'Model with same name already exists'}
    return result

# def copydatasetAtoB(datasetName,datasetNameOld,datasetCollection):
#     datasetNew = datasetCollection.find_one({"datasetName":datasetName})
#     datasetOld = datasetCollection.find_one({"datasetName":datasetNameOld})
#     for imageName in dat