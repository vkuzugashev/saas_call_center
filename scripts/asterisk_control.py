import os
import socket
import re
import platform
import subprocess
from sys import argv
import sys
import time  # Добавляем импорт модуля time

ASTERISK_PATH = '../asterisk'
IMAGE_NAME = 'asterisk'
CONTAINER_NAME = 'asterisk'

# Функция для создания Docker/Podman образа
def build_image(image_name):
    system = platform.system().lower()
    if system == 'windows':
        command = ['docker', 'build', '-t', image_name, ASTERISK_PATH]
    elif system == 'linux':
        command = ['podman', 'build', '-t', image_name, ASTERISK_PATH]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при создании образа: {result.stderr}")
    else:
        print("Контейнерный образ успешно создан.")

# Функция для запуска контейнера
def create_container(container_name, image_name):
    system = platform.system().lower()
    if system == 'windows':
        command = [
            'docker', 'create',
            '--name', container_name,
            '-p', '5060:5060/udp',
            '-p', '5038:5038',
            '-p', '10000-10100:10000-10100/udp',
            '-p', '8088:8088',
            image_name
        ]
    elif system == 'linux':
        command = [
            'podman', 'create',
            '--name', container_name,
            '-p', '5060:5060/udp',
            '-p', '5038:5038',
            '-p', '10000-10100:10000-10100/udp',
            '-p', '8088:8088',
            image_name
        ]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при создание контейнера: {result.stderr}")
    else:
        print(f"Контейнер '{container_name}' успешно создан.")

# Функция для запуска контейнера
def run_container(container_name, image_name):
    system = platform.system().lower()
    if system == 'windows':
        command = [
            'docker', 'start',
            container_name
        ]
    elif system == 'linux':
        command = [
            'podman', 'start',
            container_name
        ]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при запуске контейнера: {result.stderr}")
    else:
        print(f"Контейнер '{container_name}' успешно запущен.")

# Функция для остановки контейнера
def stop_container(container_name):
    system = platform.system().lower()
    if system == 'windows':
        command = ['docker', 'stop', container_name]
    elif system == 'linux':
        command = ['podman', 'stop', container_name]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при остановке контейнера: {result.stderr}")
    else:
        print(f"Контейнер '{container_name}' успешно остановлен.")

# Функция для удаления контейнера
def remove_container(container_name):
    system = platform.system().lower()
    if system == 'windows':
        command = ['docker', 'rm', container_name]
    elif system == 'linux':
        command = ['podman', 'rm', container_name]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при удалении контейнера: {result.stderr}")
    else:
        # Добавляем задержку на 5 секунд
        time.sleep(5)  # Пауза на 5 секунд
        print(f"Контейнер '{container_name}' успешно удален.")

# Функция для удаления образа
def remove_image(image_name):
    system = platform.system().lower()
    if system == 'windows':
        command = ['docker', 'rmi', image_name]
    elif system == 'linux':
        command = ['podman', 'rmi', image_name]
    else:
        raise RuntimeError(f"Не поддерживаемая платформа: {system}.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка при удалении образа: {result.stderr}")
    else:
        print(f"Образ '{image_name}' успешно удален.")

# Функция для получения локального IP-адреса
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Пытаемся соединиться с любым внешним сервером (Google DNS)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'  # Если не удается определить внешний IP, возвращаем localhost
    finally:
        s.close()

# Функция для замены значений в файле
def replace_ip_in_file(file_path, new_value):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Регулярное выражение для поиска полей, начинающихся с указанных значений
    pattern = r'(external_media_address|external_signaling_address|media_address)\s*=\s*\S+'
    updated_content = re.sub(pattern, lambda match: f"{match.group(1)} = {new_value}", content)

    with open(file_path, 'w') as file:
        file.write(updated_content)

def start():
   run_container(CONTAINER_NAME, IMAGE_NAME)
    
def stop():
   # Проверяем наличие контейнера и останавливаем его, если он существует
   try:
       stop_container(CONTAINER_NAME)
   except RuntimeError as e:
       if "no such container" not in str(e).lower():
           raise e

def build():
   ip_address = get_local_ip()  # Получение локального IP-адреса
   print(f"Local IP address is: {ip_address}")
   
   # Указываем путь до файла pjsip.conf
   file_path = os.path.join(ASTERISK_PATH, 'pjsip.conf')

   # Замена значений в файле
   replace_ip_in_file(file_path, ip_address)

   # Указываем путь до файла users_template.conf
   file_path = os.path.join(ASTERISK_PATH, 'users_template.conf')

   # Замена значений в файле
   replace_ip_in_file(file_path, ip_address)

   # Проверяем наличие контейнера и останавливаем его, если он существует
   try:
       stop_container(CONTAINER_NAME)
   except RuntimeError as e:
       if "no such container" not in str(e).lower():
           raise e

   # Удаляем старый контейнер, если он существует
   try:
       remove_container(CONTAINER_NAME)
   except RuntimeError as e:
       if "no such container" not in str(e).lower():
           raise e

   # Проверяем наличие образа и удаляем его, если он существует
   try:
       remove_image(IMAGE_NAME)
   except RuntimeError as e:
       err = str(e).lower()
       if "no such image" not in err and "image not known" not in err:
           raise e

   # Создание Docker/Podman образа и контейнера
   build_image(IMAGE_NAME)
   create_container(CONTAINER_NAME, IMAGE_NAME)


if __name__ == "__main__":
   if len(argv) != 2:
       print("Использование: py | python3 asterisk_control.py [start|stop|build]")
       sys.exit(1)
       
   if argv[1] == 'start':
       start()
   elif argv[1] == 'stop':
       stop()
   elif argv[1] == 'build':
       build()
   else:
       print("Неверный аргумент командной строки.")