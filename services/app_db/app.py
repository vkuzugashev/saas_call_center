import logging, pika, sys, os, json
from datetime import datetime, timezone
from model import db, table_calls, table_users, table_contacts
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
RABBIT_HOST = os.environ.get('RABBIT_HOST', 'localhost')
RABBIT_PORT = int(os.environ.get('RABBIT_PORT', '5672'))

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)
        
def run():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT))
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
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)    
    # сохраним контакт если его ещё нет
    store_contact_to_db(body)

# сохраняем звонок в базу данных
def store_to_db(body):
    with db.connect() as conn:
        call = json.loads(body)   
        ins = table_calls.insert().values(
            caller = call.get('caller'),
            callee = call.get('callee'),
            call_start = datetime.fromisoformat(call.get('start')),
            call_end = datetime.fromisoformat(call.get('end')) if call.get('end') is not None else None,
            call_status  = call.get('call_status'),
            record_file  = call.get('record_file'),
            transcription_status  = 0
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

# сохраняем контакт
def store_contact_to_db(body):
    with db.connect() as conn:
        call = json.loads(body)
        phone = call.get('caller')
        now = datetime.now(timezone.utc)
        if phone:            
            try:
                # проверяем есть ли в базе полльзователь
                user_query = table_users.select().where(table_users.c.phone == phone)            
                user = conn.execute(user_query).fetchone()
                # если пользователь есть, то завершим
                if user:
                    return

                # если нет, то проверим есть ли в базе контакт
                contact_query = table_contacts.select().where(table_contacts.c.phone == phone)
                contact = conn.execute(contact_query).fetchone()
                # если есть, то завершим
                if contact:
                    return
                
                # если нет, то добавим новый контакт
                ins = table_contacts.insert().values(
                    phone = phone,
                    name = 'новый контакт',
                    call_date = now,
                    updated_at = now
                )
                conn.execute(ins)
                conn.commit()
                logger.info(f'Contact success stored to db, call: {call}')
                return
            except Exception as e:
                logger.error(f'Contact fail store to db, call: {call}, {e}')
                return

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

