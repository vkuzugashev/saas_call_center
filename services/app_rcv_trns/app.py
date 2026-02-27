import os
import time
import logging
from dotenv import load_dotenv
import pymysql
import requests
import json

# Загрузим переменные окружения из .env файла
load_dotenv()

# Переменные окружения
# Настройки БД
DB_USER = os.getenv("DB_USERNAME")
DB_PWD = os.getenv("DB_PWD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# URL подключения к базе данных
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}/{DB_NAME}"

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# SPEECH
API_KEY = os.getenv("API_SECRET_KEY")  # Обратите внимание на переименование переменной
SPEECH_API_ENDPOINT = "https://operation.api.cloud.yandex.net//operations"

# Интервал опроса базы данных (в секундах)
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "300"))  # По умолчанию 5 минут

# Настройка логирования
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Подключение к базе данных
try:
    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USER,
                                 password=DB_PWD,
                                 database=DB_NAME,
                                 autocommit=True)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
except pymysql.err.OperationalError as e:
    logger.error(f"Ошибка подключения к базе данных: {e}")
    exit(1)


def process_dialogue(dialogue_data):
    channels = dialogue_data['response']['chunks']
    dialog_parts = []  # Список для хранения всех реплик

    # Парсим данные по каналам и добавляем в общий список
    for chunk in channels:
        channel_tag = chunk['channelTag']
        alternatives = chunk['alternatives'][0]  # Берём первую альтернативу
        words = alternatives['words']
        text = alternatives['text']

        # Собираем слова по времени
        words.sort(key=lambda x: float(x['startTime'].strip('s')))  # Сортируем слова по времени
        channel_words = [word['word'] for word in words]
        full_text = ' '.join(channel_words)

        # Добавляем в список с указанием канала и времени начала
        start_time = float(words[0]['startTime'].strip('s'))
        dialog_parts.append({
            'channel': channel_tag,
            'time': start_time,
            'text': full_text
        })

    # Сортируем по времени
    dialog_parts.sort(key=lambda x: x['time'])

    # Формируем итоговый диалог
    formatted_dialogue = ""
    for part in dialog_parts:
        formatted_dialogue += f"[{part['channel']}]: {part['text']}\n"

    return formatted_dialogue

# Функция для проверки статуса задания
def check_transcription_status(transcription_id):
    url = f'{SPEECH_API_ENDPOINT}/{transcription_id}'
    headers = {
        'Authorization': f'Api-Key {API_KEY}',  # Убедитесь, что здесь используется правильный ключ
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на успешный ответ
        return response.json()
    except requests.HTTPError as e:
        logger.error(f"Ошибка при проверке статуса транскрибации: {e}")
        return {}
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе статуса транскрибации: {e}")
        return {}

# Функция для обновления статуса транскрибации в базе данных
def update_transcription_status(transcription_id, status, result, dialog):
    response = json.dumps(result)
    cursor.execute("""
        UPDATE calls
        SET transcription = %s, transcription_status = %s, dialog = %s
        WHERE transcription_id = %s
    """, (response, status, dialog, transcription_id))
    connection.commit()

# Функция для периодической проверки статуса транскрибации
def poll_and_update_transcriptions():
    while True:
        # Получаем все записи, у которых есть transcription_id, но нет is_transcription
        cursor.execute("""
            SELECT id, transcription_id
            FROM calls
            WHERE transcription_id IS NOT NULL AND transcription_status=0
        """)
        records = cursor.fetchall()

        for record in records:
            call_id, transcription_id = record['id'], record['transcription_id']
            logger.info(f"Проверяю статус транскрибации для звонка с ID: {call_id}")

            # Получаем результат транскрибации
            response = check_transcription_status(transcription_id)
            logger.debug(f'Получен ответ: {response}')
            status = response.get('done', False)
            error = response.get('error', None)
            if status and error is None:
                logger.info("Транскрибация завершена!")
                # Обновляем запись в базе данных
                #result = response.get('response')
                dialog = process_dialogue(response)
                update_transcription_status(transcription_id, 1, response, dialog)
            elif status and error is not None:
                #result = response.get('error')
                logger.error("Возникла ошибка при выполнении транскрибации.")
                update_transcription_status(transcription_id, -1, response)  # Ставим статус -1
            else:
                logger.info(f"Статус транскрибации: {status}.")

        logger.info(f"Жду {POLLING_INTERVAL} секунд...")
        time.sleep(POLLING_INTERVAL)

# Основной цикл программы
try:
    poll_and_update_transcriptions()
except KeyboardInterrupt:
    logger.info("\nПрервано пользователем.")
finally:
    connection.close()