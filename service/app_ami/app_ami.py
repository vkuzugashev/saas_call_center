import logging
import pika, os, time, json
from dotenv import load_dotenv
from asterisk.ami import AMIClient, AutoReconnect

load_dotenv()

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
ASTERISK_HOST = os.environ.get('ASTERISK_HOST', 'localhost')
ASTERISK_PORT = int(os.environ.get('ASTERISK_PORT', '5038'))
ASTERISK_USER = os.environ.get('ASTERISK_USER', 'managerami')
ASTERISK_PWD = os.environ.get('ASTERISK_PWD', 'mysecret')
RABBIT_HOST = os.environ.get('RABBIT_HOST', 'localhost')
RABBIT_PORT = int(os.environ.get('RABBIT_PORT', '5672'))
RABBIT_EVENTS_ECHANGE = int(os.environ.get('RABBIT_EVENTS_ECHANGE', 'events'))

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger('app_ami')

def event_listener(event, **kwargs):
    logger.info(f"Принято событие: {event.name}, параметры: {event.keys}")
    publish_event(event)

def publish_event(event):
    try:
        # публикация в обменник
        channel.basic_publish(exchange=RABBIT_EVENTS_ECHANGE, routing_key='', body=json.dumps({'event': event.name, 'params': event.keys}))
        logger.info(f"Sent asterisk to queue, event: {event}")
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Ошибка подключения к RabbitMQ: {e}")
        setup_rabbitmq()
        publish_event(event)

def setup_rabbitmq():
    global connection, channel
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST, port=RABBIT_PORT))
    channel = connection.channel()
    channel.exchange_declare(exchange=RABBIT_EVENTS_ECHANGE, exchange_type='fanout')

def run():
    logger.info('Starting ...')
    setup_rabbitmq()

    client = AMIClient(address=ASTERISK_HOST, port=ASTERISK_PORT, timeout=180, encoding='ascii')
    AutoReconnect(client)
    client.add_event_listener(event_listener, white_list=['DialBegin', 'DialEnd', 'Hangup', 'VarSet'])

    future = client.login(username=ASTERISK_USER, secret=ASTERISK_PWD)
    if future.response.is_error():
        raise Exception(str(future.response))

    logger.info('Started.')

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        client.logoff()
        connection.close()
        logger.info('Stopped')

if __name__ == '__main__':
    run()
