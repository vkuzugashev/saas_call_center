import csv
import json
import os

from dotenv import load_dotenv
from flask import session
import requests

load_dotenv()

# Получение переменных окружения
APP_URL = os.getenv('APP_URL','http://localhost:5000')
MANAGER_USER = os.getenv('MANAGER_USER')
MANAGER_PWD = os.getenv('MANAGER_PWD')
ASTERISK_PATH = "../services/asterisk/conf"

# Функция для записи конфигурации в файл
def write_to_file(filename, data):
    filename = os.path.join(ASTERISK_PATH, filename)
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(data)
    except IOError as e:
        print(f"Ошибка при записи в файл {filename}: {e}")

# Функция для чтения CSV-файла и генерации конфигурации
def generate_configuration(csv_filename):
    users_configs = ["""
#include users_template.conf

"""]
    operator_members = []  # Список операторов для добавления в queue_operators.conf
    extension_configs = []  # Новый список для хранения конфигураций расширения для каждого пользователя

    try:
        with open(csv_filename, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                department = row['Отдел']
                full_name = row['ФИО']
                phone_number = row['Телефон']
                username = row['Имя пользователя']
                queue = row['Очередь']
                password = row['Пароль']

                # Формируем конфигурацию для каждого пользователя
                config = f"""
; Пользователь: {full_name}, Отдел: {department}, Телефон: {phone_number}

[{username}](internal-endpoint)
auth={username}
aors={username}

[{username}](internal-auth)
username={username}
md5_cred={password}

[{username}](internal-aor)
"""

                users_configs.append(config)

                if queue == 'operators':
                    operator_members.append(f"member => PJSIP/{username}\n")

                # Генерируем конфигурацию для extensions.conf
                # Добавление комментария перед строками конфигурации
                extension_config = f"""
; Пользователь: {full_name}, Отдел: {department}, Телефон: {phone_number}
exten => {phone_number},1,Dial(PJSIP/{username})
same => n,Hangup()
"""
                extension_configs.append(extension_config)

    except IOError as e:
        print(f"Ошибка при чтении файла {csv_filename}: {e}")

    return users_configs, operator_members, extension_configs

# Основная программа
if __name__ == '__main__':
    # Убедимся, что выходные файлы существуют
    output_files = ['users.conf', 'members_operators.conf', 'users_extensions.conf']

    # проводим вход в систему
    session = requests.Session()
    response1 = session.post(f"{APP_URL}/login", data={'username': MANAGER_USER, 'password': MANAGER_PWD})
    if response1.status_code != 200:
        print("Ошибка при входе в систему.", response1.status_code)
        exit()
    
    print("Успешный вход в систему.")

    # Запрос файла
    response = session.get(f"{APP_URL}/users/export_csv", params={'asterisk_hash': 'True'}, stream=True)
    if response.status_code != 200:
        print("Ошибка при получении файла.", response.status_code)
        exit()
    
    print("Файл успешно получен.")
    
    # Сохранение файла на диск
    with open('users.csv', 'wb') as f:
      for chunk in response.iter_content(chunk_size=1024):
         if chunk:
            f.write(chunk)
      print("Файл сохранен на диск.")

    # Генерация конфигурации
    users_configs, operator_members, extension_configs = generate_configuration('users.csv')

    # Запись в файлы
    write_to_file('users.conf', users_configs)
    print("Конфигурация успешно записана в файл users.conf.")
    write_to_file('members_operators.conf', operator_members)
    print("Конфигурация успешно записана в файл members_operators.conf.")
    write_to_file('users_extensions.conf', extension_configs)
    print("Конфигурация успешно записана в файл users_extensions.conf.")

    print("Конфигурация успешно записана в файлы.")