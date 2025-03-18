import requests
import time

# Настройки для Yandex SpeechKit
API_KEY = 'your_api_key_for_speechkit'

# Функция для проверки статуса задания
def check_transcription_status(transcription_id):
    url = f'https://operation.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize/{transcription_id}'
    headers = {
        'Authorization': f'Api-Key {API_KEY}',
    }
    response = requests.get(url, headers=headers)
    return response.json()

# Функция для проверки готовности транскрибации
def wait_for_transcription_completion(transcription_id, interval=10):
    while True:
        status = check_transcription_status(transcription_id)['status']
        if status == 'SUCCESS':
            return True
        elif status == 'FAILURE':
            return False
        time.sleep(interval)

# Пример использования
transcription_id = 'your_transcription_id'
if wait_for_transcription_completion(transcription_id):
    print("Транскрибация завершена!")
else:
    print("Возникла ошибка при выполнении транскрибации.")