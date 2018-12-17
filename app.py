#!flask/bin/python
from flask import Flask, request, jsonify
import api, constants as C, mongoDb as mongoDb, config, rabbitmqDb

app = Flask(__name__)

@app.route('/createModel', methods=['GET'])
def createModel():
    modelName = request.args.get(C.MODEL_NAME)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.createModel(modelName, modelCollection, experimentCollection)
    return jsonify(result)

@app.route('/createDataset', methods=['Get'])
def createDataset():
    modelName = request.args.get(C.MODEL_NAME)
    datasetName = request.args.get(C.DATASET_NAME)
    datasetNameOld = request.args.get(C.DATASET_NAME_OLD)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    datasetCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.DATASETCOLLECTION))
    result = api.createDataset(modelName,datasetName, modelCollection, datasetCollection)
    if datasetNameOld is not None and result["status"]== "ok":
        result = api.copydatasetAtoB(datasetName,datasetNameOld,datasetCollection)
    return jsonify(result)

@app.route('/createExperiment', methods=['GET'])
def createExperiment():
    modelName = request.args.get(C.MODEL_NAME)
    experimentName = request.args.get(C.EXPERIMENT_NAME)
    learningRate = request.args.get(C.LEARNING_RATE)
    numOfLayers = request.args.get(C.NUMBER_OF_LAYERS)
    numOfSteps = request.args.get(C.NUMBER_OF_STEPS)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.createExperiment(modelName,
                                  experimentName,
                                  learningRate,
                                  numOfLayers,
                                  numOfSteps,
                                  modelCollection,
                                  experimentCollection)
    return jsonify(result)


@app.route('/uploadTrainingImages', methods=['GET'])
def uploadImages():
    modelName = request.args.get(C.MODEL_NAME)
    imageUrls = request.args.get('image_urls')
    imageUrls = imageUrls.split(',')
    if len(imageUrls)> 3 :
        result = {"status":"ERROR","message":"TOO MANY IMAGES"}
    else:
        datasetName = None
        if request.args.get(C.DATASET_NAME):
            datasetName = request.args.get(C.DATASET_NAME)
        modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                           config.get(config.PORT),
                                                           config.get(config.DATABASENAME),
                                                           config.get(config.MODELCOLLECTION))
        datasetCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                           config.get(config.PORT),
                                                           config.get(config.DATABASENAME),
                                                           config.get(config.DATASETCOLLECTION))
        result = api.insertTrainingImages(modelName,imageUrls,modelCollection,datasetCollection,datasetName)
    return jsonify(result)

@app.route('/uploadTrainingImage', methods=['POST'])
def uploadImage():
    modelName = request.form.get(C.MODEL_NAME)
    image = request.files['file']
    datasetName = None
    if request.form.get(C.DATASET_NAME):
        datasetName = request.form.get(C.DATASET_NAME)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    datasetCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.DATASETCOLLECTION))
    result = api.insertTrainingImage(modelName,image,modelCollection,datasetCollection,datasetName)
    return jsonify(result)



@app.route('/train', methods=['GET'])
def trainModel():
    modelName = request.args.get(C.MODEL_NAME)
    experimentName = request.args.get(C.EXPERIMENT_NAME)
    datasetName = None
    if request.args.get(C.DATASET_NAME):
        datasetName = request.args.get(C.DATASET_NAME)
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
    pikapublishChannel = rabbitmqDb.getRabbitmqPublishChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    result = api.trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel,
                               datasetCollection,datasetName)
    return jsonify(result)

@app.route('/runDefaultExperiments',methods=['GET'])
def runDefaultExperiments():
    modelName = request.args.get(C.MODEL_NAME)
    if request.args.get(C.DATASET_NAME):
        datasetName = request.args.get(C.DATASET_NAME)
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
    pikapublishChannel = rabbitmqDb.getRabbitmqPublishChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    result = api.runDefaultExperiments(modelName,modelCollection,experimentCollection,pikapublishChannel,datasetCollection,datasetName)
    return jsonify(result)

@app.route('/test',methods=['POST'])
def runTest():
    modelName = request.form.get(C.MODEL_NAME)
    image = request.files['file']
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.runTest(modelName,image,modelCollection,experimentCollection)
    return jsonify(result)



@app.route('/allAccuracies',methods=['GET'])
def getAllAccuracies():
    modelName = request.args.get(C.MODEL_NAME)
    experimentName = None
    if request.args.get(C.EXPERIMENT_NAME):
        experimentName = request.args.get(C.EXPERIMENT_NAME)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.getAllAccuracies(modelName, experimentCollection, modelCollection, experimentName,False)
    return jsonify(result)

@app.route('/bestAccuracy',methods=['GET'])
def getBestAccuracy():
    modelName = request.args.get(C.MODEL_NAME)
    bestAccuracyFlag = True
    experimentName = None
    if request.args.get(C.EXPERIMENT_NAME):
        experimentName = request.args.get(C.EXPERIMENT_NAME)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.getAllAccuracies(modelName, experimentCollection, modelCollection, experimentName,bestAccuracyFlag)
    return jsonify(result)





if __name__ == '__main__':
    app.run(host='localhost',debug=True)