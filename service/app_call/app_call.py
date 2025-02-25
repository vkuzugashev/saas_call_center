import logging
import pika, sys, os, redis, json, re, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log_level = os.environ.get('LOG_LEVEL', 'INFO')
rabbit_host = os.environ.get('RABBIT_HOST')
rabbit_port = int(os.environ.get('RABBIT_PORT', '5672'))
redis_host = os.environ.get('REDIS_HOST')
redis_port = int(os.environ.get('REDIS_PORT', '6379'))
client_url = os.environ.get('CLIENT_URL', None)

logging.basicConfig(level=log_level)
logger = logging.getLogger('app_call')

def uniqueid_to_timestamp(uniqueid):
    ts = int(re.search('\d{10}', uniqueid)[0])
    return ts

def get_redis_client():
    pool = redis.ConnectionPool(host=redis_host, port=redis_port)
    return redis.Redis(connection_pool=pool)

def redis_get(key):
    r = get_redis_client()
    value = r.get(key)
    logger.debug(f'Get from redis: {key} -> {value}')
    if value is not None:
        return json.loads(value)
    else:
        return None
    
def redis_set(key, value):
    r = get_redis_client()
    str_call = json.dumps(value)
    r.set(key, str_call, ex=3600)
    logger.debug(f'Stored in redis: {key} -> {str_call}')
    
def get_client_id(msisdn):
    if client_url is not None:
        response = requests.get(f'{client_url}/{msisdn}')
        content = response.content
        if response.status_code == 200:
            data = json.loads(content)
            client_id = data.get('client_id')
            logger.info(f'Got client_id: {client_id}')
            return client_id
        elif response.status_code == 404:
            return None
    else:
        return None

def dial_begin(uniqueid, caller, callee, start, call_status):
    caller_id = get_client_id(caller)
    call = {'uniqueid': uniqueid,
            'start': start, 
            'end': None, 
            'caller': caller, 
            'callee': callee, 
            'caller_id': caller_id, 
            'callee_id': None, 
            'call_status': call_status, 
            'record_file': None, 
            'record_file_in': None, 
            'record_file_out': None}    
    logger.info(f'DialBegin, start processing, call: {call}')    
    redis_set(uniqueid, call)
    logger.info(f'DialBegin processed, call stored in redis: {call}')

def varset(uniqueid, record_file):
    call = redis_get(uniqueid)
    logger.info(f'VarSet, start processing, call: {call}, record_file: {record_file}')  
    if call is not None:
        record_file =  record_file.replace("/var/spool/asterisk/monitor", "")
        name, ext = os.path.splitext(record_file)
        record_file_in =  f"{name}-in{ext}"
        record_file_out =  f"{name}-out{ext}"
        call['record_file'] = record_file  
        call['record_file_in'] = record_file_in 
        call['record_file_out'] = record_file_out 
        redis_set(uniqueid, call)
        logger.info(f'VarSet processed, call stored in redis: {call}')  
    else:
        logger.error(f'VarSet processed, redis have`t key: {uniqueid}, call: {call}')        

def dial_end(uniqueid, call_status):
    call = redis_get(uniqueid)
    logger.info(f'DialEnd, start processing, call: {call}')    
    if call is not None:
        call['call_status'] = call_status
        redis_set(uniqueid, call)
        logger.info(f'DialEnd processed, call stored in redis: {call}')
    else:
        logger.error(f'DialEnd processed, redis have`t key: {uniqueid}, call: {call}')
   
def hangup(uniqueid, end):
    logger.info(f'HangUp, start processing, uniqueid: {uniqueid}')
    call = redis_get(uniqueid)
    if call is not None:
        if call['call_status'] == 'ANSWER':
            call['end'] = end
        redis_set(uniqueid, call)
        store_to_queue(call)
        logger.info(f'HangUp processed, call stored in queue: {call}')
    else:
        logger.error(f'HangUp processed, redis have`t key: {uniqueid}')

def store_to_queue(call,**kwargs):
    with pika.BlockingConnection(pika.ConnectionParameters(rabbit_host, port=rabbit_port)) as connection:
        channel = connection.channel()    
        channel.queue_declare(queue='calls')
        channel.basic_publish(exchange='',
                              routing_key='calls',
                              body=json.dumps(call))
    
def set_call(key):
    r = get_redis_client()
    r.setex(key, 60)
    
def event_parse_and_route(body):    
    event = json.loads(body)
   
    if event['event'] == 'DialBegin':
        # начало дозвона
        uniqueid = event['params']['Uniqueid']        
        caller = event['params']['CallerIDNum']
        callee = event['params']['DestCallerIDNum']
        # todo сделать конвертацию в timestamp с милисекундами, сейчас мы их отбрасываем
        ts = uniqueid_to_timestamp(uniqueid)
        start = datetime.fromtimestamp(ts).isoformat()  #.strftime('%Y-%m-%d %H:%M:%S')     
        call_status = event['params']['ChannelStateDesc']
        dial_begin(uniqueid, caller, callee, start, call_status)
        
    elif event['event'] == 'DialEnd' and event['params']['DialStatus'] in ['CANCEL','BUSY','NOANSWER','ANSWER']:
        # Конец дозвона
        uniqueid = event['params']['Uniqueid']
        call_status = event['params']['DialStatus']
        dial_end(uniqueid, call_status)
                
    elif event['event'] == 'Hangup':
        # Конц вызова абонент повешал трубку
        uniqueid = event['params']['Linkedid']
        end = datetime.now().isoformat() #.strftime('%Y-%m-%d %H:%M:%S')   
        hangup(uniqueid, end)

    elif event['event'] == 'VarSet' and event['params']['Variable'] == 'MIXMONITOR_FILENAME':
        # запись аудео файла
        uniqueid = event['params']['Linkedid']
        record_file = event['params']['Value']
        varset(uniqueid, record_file)    
    
    #else:
    #    logger.info(f'Unknow event: {body}')

def callback(ch, method, properties, body):    
    #logger.info(f'Received new event: {body}')
    event_parse_and_route(body)
        
def run():
    with pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host)) as connection:
        channel = connection.channel()
        channel.queue_declare(queue='events')   
        channel.basic_consume(queue='events', auto_ack=True, on_message_callback=callback)
        logger.info('[*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
