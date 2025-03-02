import logging, pika, sys, os, json
from datetime import datetime
from model import db, table_calls
from dotenv import load_dotenv

load_dotenv()

log_level = os.environ.get('LOG_LEVEL', 'INFO')
rabbit_host = os.environ.get('RABBIT_HOST', 'localhost')
rabbit_port = int(os.environ.get('RABBIT_PORT', '5672'))

logging.basicConfig(level=log_level)
logger = logging.getLogger('app_db')
        
def run():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, port=rabbit_port))
    channel = connection.channel()
    channel.queue_declare(queue='calls')   
    channel.basic_consume(queue='calls', auto_ack=False, on_message_callback=callback)
    logger.info('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def callback(ch, method, properties, body):    
    logger.info(f'Received call {body}')
    result = store_to_db(body)
    if result:
        ch.basic_ack(delivery_tag = method.delivery_tag)

def store_to_db(body):
    with db.connect() as conn:
        call = json.loads(body)   
        ins = table_calls.insert().values(
            #id = 1,
            caller = call.get('caller'),
            callee = call.get('callee'),
            caller_id = call.get('caller_id'),
            callee_id = call.get('callee_id'),
            call_start = datetime.fromisoformat(call.get('start')),
            call_end = datetime.fromisoformat(call.get('end')) if call.get('end') is not None else None,
            call_status  = call.get('call_status'),
            record_file  = call.get('record_file'),
            record_file_in  = call.get('record_file_in'),
            record_file_out  = call.get('record_file_out')
        )
        try:
            conn.execute(ins)
            conn.commit()
            logger.info(f'Call success stored to db, call: {call}')
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f'Call fail store to db, call: {call}, {e}')
            return False

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

