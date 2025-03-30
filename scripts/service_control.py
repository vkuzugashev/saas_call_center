import os
import subprocess
import random
import string
import sys

SERVICE_PATH = '../service/'

def generate_password(length=10):
   """
   Функция для генерации случайного пароля.

   Args:
       length (int): Длина пароля.

   Returns:
       str: Сгенерированный пароль.
   """
   letters = string.ascii_letters + string.digits
   return ''.join(random.choice(letters) for i in range(length))

def create_image(image_name, dockerfile_path):
   """
   Функция для создания Docker образа.

   Args:
       image_name (str): Имя образа.
       dockerfile_path (str): Путь до Dockerfile.

   Returns:
       None
   """
   command = ['docker', 'build', '-t', image_name, '-f', dockerfile_path, '.']
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании образа: {result.stderr}")
   else:
       print(f"Образ {image_name} успешно создан.")

def create_container(container_name, image_name, env_vars):
   """
   Функция для создания Docker контейнера.

   Args:
       container_name (str): Имя контейнера.
       image_name (str): Имя образа.
       env_vars (dict): Словарь с переменными окружения.

   Returns:
       None
   """
   env_args = []
   for key, value in env_vars.items():
       env_args.extend(['-e', f'{key}={value}'])

   command = ['docker', 'create', '--name', container_name] + env_args + [image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании контейнера: {result.stderr}")
   else:
       print(f"Контейнер {container_name} успешно создан.")

def start_container(container_name):
   """
   Функция для запуска Docker контейнера.

   Args:
       container_name (str): Имя контейнера.

   Returns:
       None
   """
   command = ['docker', 'start', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при запуске контейнера: {result.stderr}")
   else:
       print(f"Контейнер {container_name} успешно запущен.")

def stop_container(container_name):
   """
   Функция для остановки Docker контейнера.

   Args:
       container_name (str): Имя контейнера.

   Returns:
       None
   """
   command = ['docker', 'stop', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при остановке контейнера: {result.stderr}")
   else:
       print(f"Контейнер {container_name} успешно остановлен.")

def build():
   """
   Функция для создания сервисов.
   """
   # Генерация пароля для root пользователя БД
   db_password = generate_password()

   rabbitmq_path = os.path.join(SERVICE_PATH, 'rabbitmq/dockerfile')
   redis_path = os.path.join(SERVICE_PATH, 'redis/dockerfile')
   mariadb_path = os.path.join(SERVICE_PATH, 'mariadb/dockerfile')

   # Создание образов
   create_image('rabbitmq', rabbitmq_path)
   create_image('redis', redis_path)
   create_image('mariadb', mariadb_path)

   # Запись пароля в .env файл
   with open('.env', 'w') as f:
       f.write(f'MARIADB_ROOT_PASSWORD={db_password}\n')

   # Запуск контейнеров
   create_container('rabbitmq', 'rabbitmq', {})
   create_container('redis', 'redis', {})
   create_container('mariadb', 'mariadb', {
       'MARIADB_ROOT_PASSWORD': db_password,
       'MARIADB_DATABASE': 'call_center'})

def start():
   """
   Функция для запуска сервисов.
   """
   # Запуск контейнеров
   start_container('rabbitmq')
   start_container('redis')
   start_container('mariadb')

def stop():
   """
   Функция для остановки сервисов.
   """
   # Остановка контейнеров
   stop_container('rabbitmq')
   stop_container('redis')
   stop_container('mariadb')

if __name__ == '__main__':
   if len(sys.argv) != 2:
       print("Использование: py | python3 service_control.py [build|start|stop]")
       sys.exit(1)
   
   command = sys.argv[1]
   
   if command == 'build':
       build()
   elif command == 'start':
       start()
   elif command == 'stop':
       stop()
   else:
       print("Недопустимая команда.")
       sys.exit(1)
       