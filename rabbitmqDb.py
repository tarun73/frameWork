import pika
import config

rabbitMqconnection = None
rabbitMqPublishChannel = None
rabbitMqConsumeChannel = None

def getRabbitMqConnection(host):
    global rabbitMqconnection
    if rabbitMqconnection is None :
        rabbitMqconnection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host,heartbeat_interval=0,
                                      credentials=pika.PlainCredentials(config.get(config.PIKA_ID),config.get(config.PIKA_PASSWORD))))
    if rabbitMqconnection.is_closed :
        rabbitMqconnection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    return rabbitMqconnection

def getRabbitmqPublishChannel(host,defaultQueueToUse):
    global rabbitMqPublishChannel
    if rabbitMqPublishChannel is None or rabbitMqPublishChannel.is_closed or rabbitMqPublishChannel.is_closing:
        rabbitMqConnection = getRabbitMqConnection(host=host)
        rabbitMqPublishChannel = rabbitMqConnection.channel()
        rabbitMqPublishChannel.queue_declare(queue=defaultQueueToUse, durable=True)
    elif rabbitMqPublishChannel.is_open :
        rabbitMqPublishChannel =rabbitMqPublishChannel
    return rabbitMqPublishChannel

def getRabbitmqConsumeChannel(host,defaultQueueToUse):
    global rabbitMqConsumeChannel
    if rabbitMqConsumeChannel is None or rabbitMqConsumeChannel.is_closed or rabbitMqConsumeChannel.is_closing:
        rabbitMqConnection = getRabbitMqConnection(host=host)
        rabbitMqConsumeChannel = rabbitMqConnection.channel()
        rabbitMqConsumeChannel.queue_declare(queue=defaultQueueToUse, durable=True)
    elif rabbitMqConsumeChannel.is_open :
        rabbitMqConsumeChannel =rabbitMqConsumeChannel
    return rabbitMqConsumeChannel
