import sys, os, logging, json 
import asyncio, aiormq, requests, time
from websockets import serve
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
rabbit_host = os.environ.get('RABBIT_HOST', 'localhost')
WEBSOCKET_HOST = os.environ.get('WEBSOCKET_HOST', 'localhost')
WEBSOCKET_PORT = os.environ.get('WEBSOCKET_PORT', 5078)
CLIENT_INFO_URL = os.environ.get('CLIENT_INFO_URL', 'http://localhost:8000/clients')
AMQP_QUEUE = os.environ.get('RABBIT_EVENTS_QUEUE', 'events')
AMQP_URL = f'amqp://{rabbit_host}/'
LAST_ACTIVITY_TIMEOUT = 30  # Время неактивности в секундах

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger('app_new_call')

clients = set()
lock = asyncio.Lock()

@lru_cache(maxsize=None)
def get_client_info(msisdn):
    """Функция для получения информации о клиенте по MSISDN"""
    response = requests.get(f'{CLIENT_INFO_URL}/{msisdn}')
    content = response.json()
    if response.status_code == 200:
        return content
    elif response.status_code == 404:
        return None
    else:
        raise Exception(f"Получен неожидаемый статус код: {response.status_code}")

# async def check_websocket_clients_activity():
#     global clients
#     while True:
#         current_time = time.time()
#         async with lock:
#             inactive_clients = [client for client in clients if current_time - client.last_activity > LAST_ACTIVITY_TIMEOUT]
#             for client in inactive_clients:
#                 logger.info(f"Закрыть не активное соедиенение: {client.remote_address}")
#                 await client.close()
#                 clients.remove(client)
#             await asyncio.sleep(LAST_ACTIVITY_TIMEOUT / 2)

async def handle_incoming_message(message):    
    """Обработчик входящих сообщений из очереди RabbitMQ"""
    try:
        logger.info(f'Received {message.body}')
        event = json.loads(message.body)
        # начало дозвона
        if event['event'] == 'DialBegin':
            caller = event['params']['CallerIDNum']
            message = get_client_info(caller)
            if message is not None:        
                if clients:
                    logger.info('Отправка websocket клиентам сообщения:', message)
                    await asyncio.wait([client.send(message) for client in clients])
    except KeyError as e:
        logger.error(f"KeyError occurred: {e}. Event data: {event}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}. Message body: {message.body}")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")

async def consummer():
    """Функция для потребления сообщений из очереди"""
    logger.debug('Start consuming')
    connection = None
    while True:
        try:
            logger.debug(f'Check connection ...')
            if connection is None or connection.is_closed:
                connection = await aiormq.connect(AMQP_URL)
                channel = await connection.channel()
                declare_ok = await channel.queue_declare(queue=AMQP_QUEUE)
                await channel.basic_consume(declare_ok.queue, handle_incoming_message, no_ack=True)  
                logger.info('Ожидание сообщений.')
            else:
                await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {AMQP_URL}, {e}")
            await asyncio.sleep(10)  # Ждем 10 секунд перед повторной попыткой
            connection = None

async def websocket_handler(websocket):
    """Обработка нового WebSocket-соединения"""
    global clients
    clients.add(websocket)
    logger.info(f'Подключен websocket: {websocket.remote_address}')
    try:
        async for message in websocket:
            logger.info(f'Получено сообщение из websocket: {message}')
    finally:
        async with lock:
            clients.remove(websocket)
            logger.info(f'Удален websocket: {websocket.remote_address}')

async def producer():
    """Обработка WebSocket-соединений"""
    global clients
    wss = None
    while True:
        try:
            if wss is None or not wss.is_serving:
                logger.info('Ожидание сообщений из websocket.')
                wss = await serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT)
        except OSError as e:
            logger.error(f"Ошибка сетевого подключения: {e}")
        except asyncio.InvalidStateError as e:
            logger.error(f"Некорректное состояние WebSocket: {e}")
        except Exception as e:
            logger.error(f"Необработанная ошибка: {e}")
        await asyncio.sleep(10)

async def main():
    """Основная функция запуска сервера."""
    await asyncio.gather(
        producer(), 
        consummer())
#        check_websocket_clients_activity())

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
