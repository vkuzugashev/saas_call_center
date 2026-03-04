import sys, os, logging, json 
import asyncio, aiormq
from websockets import serve
from dotenv import load_dotenv
from functools import lru_cache
from models.model import db, table_users, table_contacts

load_dotenv()

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
RABBIT_HOST = os.environ.get('RABBIT_HOST')
WEBSOCKET_HOST = os.environ.get('APP_NEW_CALL_WEBSOCKET_HOST')
WEBSOCKET_PORT = os.environ.get('APP_NEW_CALL_WEBSOCKET_PORT')
RABBIT_EVENTS_EXCHANGE = os.environ.get('RABBIT_EVENTS_EXCHANGE')
RABBIT_APP_NEW_CALL_EVENTS_QUEUE = os.environ.get('RABBIT_APP_NEW_CALL_EVENTS_QUEUE')

AMQP_URL = f'amqp://{RABBIT_HOST}/'
LAST_ACTIVITY_TIMEOUT = 30  # Время неактивности в секундах

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

clients = set()
lock = asyncio.Lock()

@lru_cache(maxsize=None)
def get_contact_info(msisdn):
    """Функция для получения информации о клиенте по MSISDN"""
    contact = { 'msisdn': msisdn, 'contracts': () }

    try:
        with db.connect() as conn:
            query = table_users.select(table_users.c.phone == msisdn)
            result = conn.execute(query)
            row = result.fetchone()
            if row:
                contact['client_id'] = row[table_users.c.fio]
                return contact

            query = table_contacts.select(table_contacts.c.phone == msisdn)
            result = conn.execute(query)
            row = result.fetchone()
            if row:
                contact['client_id'] = row[table_contacts.c.name]
                contact['contracts'] = row[table_contacts.c.orders]
                return contact

            logger.debug(f"Не найден клиент с номером {msisdn}.")
            return None
    except Exception as e:
        logger.error(f"Ошибка при запросе информации о клиенте: {e}")
        return None

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

def get_default_client_info(msisdn):
    return {'msisdn': msisdn, 'client_id': 'Неизвестный номер', 'contracts': ()}

async def handle_incoming_message(message):    
    """Обработчик входящих сообщений из очереди RabbitMQ"""
    try:
        logger.info(f'Received {message.body}')
        event = json.loads(message.body)
        # начало дозвона
        if event['event'] == 'DialBegin':
            caller = event['params']['CallerIDNum']
            message = get_contact_info(caller)
            if message is None:
                message = get_default_client_info(caller)
                       
            if clients:
                text = json.dumps(message)
                logger.info('Отправка websocket клиентам сообщения:', text)
                for client in clients:
                    await client.send(text) 
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
                await channel.exchange_declare(exchange=RABBIT_EVENTS_EXCHANGE, exchange_type='fanout')
                # используем временную очередь
                declare_ok = await channel.queue_declare(queue=RABBIT_APP_NEW_CALL_EVENTS_QUEUE)
                await channel.queue_bind(exchange=RABBIT_EVENTS_EXCHANGE, queue=declare_ok.queue)
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
