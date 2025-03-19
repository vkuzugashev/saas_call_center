import os
import tempfile
from dotenv import load_dotenv
import pymysql
import requests
import time
import logging
import boto3
from botocore.client import Config

# Загрузим переменные окружения из .env файла
load_dotenv()

# Переменные окружения
# Настройки БД
DB_USER = os.getenv("DB_USER")
DB_PWD = os.getenv("DB_PWD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# URL подключения к базе данных
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}/{DB_NAME}"

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Настройки для Yandex Object Storage
YOS_ACCESS_KEY_ID = os.getenv("YOS_ACCESS_KEY_ID")
YOS_SECRET_ACCESS_KEY = os.getenv("YOS_SECRET_ACCESS_KEY")
YOS_BUCKET_NAME = "penart-record"
YOS_REGION = "ru-central1"

# SPEECH
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
SPEECH_API_ENDPOINT = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"

# Интервал опроса базы данных (в секундах)
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "900"))  # По умолчанию 15 минут

RECORD_URL_PREFIX  = os.getenv('RECORD_URL_PREFIX','http://localhost:8088/static/monitor')

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

# Создаем временный каталог для скачиваемых файлов
TEMP_DIR = tempfile.mkdtemp()

# Функция для скачивания файла по ссылке
def download_file(record_file, save_path):
    url = RECORD_URL_PREFIX +'/'+ record_file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Проверка успешного ответа
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"Файл успешно скачан и сохранен в {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при скачивании файла: {e}")
        return None

# Функция для загрузки файла в Yandex Object Storage
def upload_file_to_yos_bucket(file_path, object_name):
    session = boto3.session.Session()
    s3 = session.resource(
        service_name="s3",
        endpoint_url=f"https://storage.yandexcloud.net",
        aws_access_key_id=YOS_ACCESS_KEY_ID,
        aws_secret_access_key=YOS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name=YOS_REGION
    )

    bucket = s3.Bucket(YOS_BUCKET_NAME)
    bucket.upload_file(file_path, object_name)
    uploaded_url = f"https://storage.yandexcloud.net/{YOS_BUCKET_NAME}/{object_name}"
    logger.info(f"Файл успешно загружен в Yandex Object Storage: {uploaded_url}")

    # Возвращаем публичную ссылку на файл
    return uploaded_url

# Функция для отправки запроса на распознавание речи
def recognize_audio(record_file):
    headers = {"Authorization": f"Api-Key {API_SECRET_KEY}"}
    payload = {"config": {
                    "specification": { 
                        "audioEncoding": "LINEAR16_PCM", 
                        "sampleRateHertz": "8000",
                        "audioChannelCount": 2,
                        "languageCode": "ru-RU"
                    }
                }, 
                "audio": {
                    "uri": record_file
                }
            }
    
    retries = 0
    while retries < 3:  # Максимум 3 попытки
        try:
            response = requests.post(SPEECH_API_ENDPOINT, headers=headers, json=payload)
            if response.ok:
                return response.json().get("id")
            else:
                logger.error(f"Ошибка распознавания речи: статус-код {response.status_code}")
                retries += 1
                continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отправки запроса на распознавание: {e}")
            retries += 1
            continue
    return None

# Основная функция для периодического опроса базы данных
def poll_and_process_records():
    while True:
        cursor.execute("""
            SELECT id, record_file
            FROM calls
            WHERE call_status='ANSWER' and record_file is not null and transcription_id IS NULL
            LIMIT 100  # Ограничиваем количество записей для одной итерации
        """)
        records = cursor.fetchall()

        for record in records:
            call_id, record_file = record["id"], record["record_file"]
            logger.info(f"Пытаемся распознать звонок с ID: {call_id}")
            
            # Скачиваем файл
            downloaded_file_path = os.path.join(TEMP_DIR, f"{call_id}.wav")
            if download_file(record_file, downloaded_file_path):
                # Загружаем файл в Yandex Object Storage
                yos_object_name = f"{call_id}.wav"
                yos_file_uri = upload_file_to_yos_bucket(downloaded_file_path, yos_object_name)                
                transcription_id = recognize_audio(yos_file_uri)
                if transcription_id:
                    cursor.execute("""
                        UPDATE calls
                        SET transcription_id = %s
                        WHERE id = %s
                    """, (transcription_id, call_id))
                    logger.info(f"Успешно создано задание с transcription_id: {transcription_id}")
                else:
                    logger.warning(f"Не создать задание с ID: {call_id}")
                # Удаляем временный файл после обработки
                try:
                    os.remove(downloaded_file_path)
                except OSError as e:
                    logger.error(f"Ошибка при удалении временного файла: {e}")
            else:
                logger.error(f"Не удалось скачать файл для звонка с ID: {call_id}")

        logger.info(f"Жду {POLLING_INTERVAL} секунд...")
        time.sleep(POLLING_INTERVAL)

try:
    poll_and_process_records()
except KeyboardInterrupt:
    logger.info("\nПрервано пользователем.")
finally:
    connection.close()