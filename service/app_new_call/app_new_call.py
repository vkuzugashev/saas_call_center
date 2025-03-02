import sys, os, logging, json, re, requests, websockets, asyncio, aiormq, random, asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log_level = os.environ.get('LOG_LEVEL', 'INFO')
rabbit_host = os.environ.get('RABBIT_HOST', 'localhost')

logging.basicConfig(level=log_level)
logger = logging.getLogger('app_new_call')


clients = set()

def uniqueid_to_timestamp(uniqueid):
    ts = int(re.search('\d{10}', uniqueid)[0])
    return ts
    
def get_client_info(msisdn):
    response = requests.get(f'http://127.0.0.1:8000/clients/{msisdn}')
    #content = response.content
    content = response.json()
    if response.status_code == 200:
        return content
    elif response.status_code == 404:
        return None

def dial_begin(uniqueid, caller, callee, start, call_status):
    message = get_client_info(caller)
    if message != None:        
        logger.info('dial_begin wwith message:', message)
        websockets.broadcast(clients, json.dumps(message))
        # websockets.broadcast(clients, json.dumps(caller))

def dial_end(uniqueid, call_status):
    None
   
def hangup(uniqueid, end):
    None
    
def event_parse_and_route(body):    
    event = json.loads(body)
    logger.info('Get event:', event)
    
    if event['event'] == 'DialBegin':
        # начало дозвона
        uniqueid = event['params']['Uniqueid']        
        caller = event['params']['CallerIDNum']
        callee = event['params']['DestCallerIDNum']
        # todo сделать конвертацию в timestamp с милисекундами, сейчас мы их отбрасываем
        ts = uniqueid_to_timestamp(uniqueid)
        start = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')     
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
        end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   
        hangup(uniqueid, end)
    
    else:
        logger.warn('Unknow event:', body)

async def on_message(message):    
    logger.info(f' [x] Received {message.body}')
    event_parse_and_route(message.body)

async def handler(websocket):
    clients.add(websocket)
    try:
        # Broadcast a message to all connected clients.
        # await asyncio.sleep(1)
        # message = dial_begin()
        websockets.broadcast(clients, json.dumps({'hello': 'message'}))
        while True:
            await asyncio.sleep(1)
    finally:
        # Unregister.
        #clients.remove(websocket)
        None

async def start_consumming():
    print(' [*] Waiting event messages. To exit press CTRL+C')
    # Perform connection
    connection = await aiormq.connect("amqp://guest:guest@localhost/")
    # Creating a channel
    channel = await connection.channel()
    # Declaring queue
    declare_ok = await channel.queue_declare('events')
    consume_ok = await channel.basic_consume(declare_ok.queue, on_message, no_ack=True)  

async def start_websocket_serv():
    print(' [*] Waiting connection for websocket. To exit press CTRL+C')
    #await asyncio.sleep(10)
    async with websockets.serve(handler, "localhost", 5678):
        await asyncio.Future()  # run forever

async def main(): 
    await asyncio.gather(start_consumming(), start_websocket_serv())

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
