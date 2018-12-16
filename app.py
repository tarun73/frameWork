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

@app.route('/uploadTrainingImages', methods=['POST'])
def uploadImages():
    modelName = request.args.get(C.MODEL_NAME)
    imageUrls = request.form.getlist('image_urls')
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    api.insertTrainingImages(modelName,imageUrls,modelCollection)
    return

@app.route('/uploadTrainingImage', methods=['POST'])
def uploadImage():
    modelName = request.form.get(C.MODEL_NAME)
    image = request.files['file']
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    result = api.insertTrainingImage(modelName,image,modelCollection)
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

@app.route('/train', methods=['GET'])
def trainModel():
    modelName = request.args.get(C.MODEL_NAME)
    experimentName = request.args.get(C.EXPERIMENT_NAME)
    # trainingSetNumber = request.args.get(C.TRAINING_SET_NUM)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    pikapublishChannel = rabbitmqDb.getRabbitmqPublishChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    result = api.trainTheModel(modelName,experimentName,modelCollection,experimentCollection,pikapublishChannel)
    return jsonify(result)

@app.route('/runDefaultExperiments',methods=['GET'])
def runDefaultExperiments():
    modelName = request.args.get(C.MODEL_NAME)
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    pikapublishChannel = rabbitmqDb.getRabbitmqPublishChannel(config.get(config.PIKA_HOST),C.TRAINING_QUEUE_NAME)
    result = api.runDefaultExperiments(modelName,modelCollection,experimentCollection,pikapublishChannel)
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
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.getAllAccuracies(modelName, experimentCollection, modelCollection, False)
    return jsonify(result)

@app.route('/bestAccuracy',methods=['GET'])
def getBestAccuracy():
    modelName = request.args.get(C.MODEL_NAME)
    bestAccuracyFlag = True
    modelCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.MODELCOLLECTION))
    experimentCollection = mongoDb.getMongoCollectionClient(config.get(config.HOST),
                                                       config.get(config.PORT),
                                                       config.get(config.DATABASENAME),
                                                       config.get(config.EXPERIMENTCOLLECTION))
    result = api.getAllAccuracies(modelName, experimentCollection, modelCollection, bestAccuracyFlag)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)