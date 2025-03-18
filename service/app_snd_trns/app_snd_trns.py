import pika
import json
import os
import requests

# Настройки подключения к RabbitMQ
RABBITMQ_HOST = 'your-rabbitmq-host'
RABBITMQ_PORT = 5672
QUEUE_NAME = 'your_queue_name'

# Настройки для работы с Yandex SpeechKit
API_KEY = 'your_api_key_for_speechkit'

# Функция для скачивания файла по ссылке
def download_file(url, local_path):
    response = requests.get(url)
    with open(local_path, 'wb') as file:
        file.write(response.content)

# Функция для загрузки файла в Yandex Object Storage
def upload_file_to_yandex_storage(file_path, object_name):
    # Логика загрузки файла в Yandex Object Storage...
    pass

# Функция для инициации асинхронного распознавания речи
def initiate_asynchronous_recognition(audio_url, language='ru-RU'):
    url = 'https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize'
    headers = {
        'Authorization': f'Api-Key {API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'config': {
            'specification': {
                'languageCode': language
            }
        },
        'uri': audio_url
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()['id']

# Функция для обработки сообщений из очереди RabbitMQ
def callback(ch, method, properties, body):
    # Извлекаем имя файла из сообщения
    message = json.loads(body.decode('utf-8'))
    record_file = message['record_file']

    # Скачиваем файл
    local_file_path = f'/tmp/{os.path.basename(record_file)}'
    download_file(record_file, local_file_path)
    print(f'File downloaded to {local_file_path}')

    # Загружаем файл в Yandex Object Storage
    object_name = os.path.basename(local_file_path)
    object_url = upload_file_to_yandex_storage(local_file_path, object_name)
    print(f'File uploaded to Yandex Object Storage: {object_url}')

    # Инициируем асинхронное распознавание речи
    recognition_id = initiate_asynchronous_recognition(object_url)
    print(f'Aynchronous recognition initiated with ID: {recognition_id}')

    # Удаляем локальный файл
    os.remove(local_file_path)
    print(f'Local file removed: {local_file_path}')

    ch.basic_ack(delivery_tag=method.delivery_tag)

# Подключение к RabbitMQ и подписка на очередь
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT))
channel = connection.channel()

channel.queue_declare(queue=QUEUE_NAME, durable=True)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

print('Waiting for messages. To exit press CTRL+C')
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()

connection.close()