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
   command = ['docker', 'build', '-t', image_name, dockerfile_path]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании образа: {result.stderr}")
   else:
       print(f"Образ {image_name} успешно создан.")

def create_container(container_name, image_name, env_vars, ports):
   """
   Функция для создания Docker контейнера.

   Args:
       container_name (str): Имя контейнера.
       image_name (str): Имя образа.
       env_vars (dict): Словарь с переменными окружения.
       ports (dict): Словарь с открытыми портами.

   Returns:
       None
   """
   env_args = []
   for key, value in env_vars.items():
       env_args.extend(['-e', f'{key}={value}'])

   port_args = []
   for host_port, container_port in ports.items():
       port_args.extend(['-p', f'{host_port}:{container_port}'])

   command = ['docker', 'create', '--name', container_name] + env_args + port_args + [image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании контейнера: {result.stderr}")
   else:
       print(f"Контейнер {container_name} успешно создан.")

def remove_container(container_name):
   """
   Функция для удаления Docker контейнера.

   Args:
      container_name (str): Имя контейнера.

   Returns:
      None
      """
   # Удаление контейнера
   command = ['docker', 'rm', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      raise RuntimeError(f"Ошибка при удалении контейнера: {result.stderr}")
   else:
      print(f"Контейнер {container_name} успешно удален.")


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
   rabbitmq_path = os.path.join(SERVICE_PATH, 'rabbitmq')
   redis_path = os.path.join(SERVICE_PATH, 'redis')
   mariadb_path = os.path.join(SERVICE_PATH, 'mariadb')
   app_ami_path = os.path.join(SERVICE_PATH, 'app_ami')
   app_call_path = os.path.join(SERVICE_PATH, 'app_call')
   app_db_path = os.path.join(SERVICE_PATH, 'app_db')
   app_new_call_path = os.path.join(SERVICE_PATH, 'app_new_call')
   app_rcv_path = os.path.join(SERVICE_PATH, 'app_rcv_trns')
   app_snd_path = os.path.join(SERVICE_PATH, 'app_snd_trns')

   db_password = os.environ.get('MARIADB_ROOT_PASSWORD')
   if not db_password:
      # Генерация пароля для root пользователя БД
      db_password = generate_password()
      # Запись пароля в .env файл
      with open('.env', 'w') as f:
         f.write(f'MARIADB_ROOT_PASSWORD={db_password}\n')   

   # Остановка и удаление контейнеров
   stop_container('rabbitmq')
   stop_container('redis')
   stop_container('mariadb')
   stop_container('app_ami')
   stop_container('app_call')
   stop_container('app_db')
   stop_container('app_new_call')
   stop_container('app_rcv')
   stop_container('app_snd')

   # Удаление контейнеров
   remove_container('rabbitmq')
   remove_container('redis')
   remove_container('mariadb')
   remove_container('app_ami')
   remove_container('app_call')
   remove_container('app_db')
   remove_container('app_new_call')
   remove_container('app_rcv')
   remove_container('app_snd')

   # Создание образов
   create_image('rabbitmq', rabbitmq_path)
   create_image('redis', redis_path)
   create_image('mariadb', mariadb_path)
   create_image('app_ami', app_ami_path)
   create_image('app_call', app_call_path)
   create_image('app_db', app_db_path)
   create_image('app_new_call', app_new_call_path)
   create_image('app_rcv', app_rcv_path)
   create_image('app_snd', app_snd_path)

   # Запуск контейнеров
   create_container('rabbitmq', 'rabbitmq', {},{})
   create_container('redis', 'redis', {}, {'6379': '6379'})
   create_container('mariadb', 'mariadb', {
       'MARIADB_ROOT_PASSWORD': db_password,
       'MARIADB_DATABASE': 'call_center'},
       {'3306': '3306'})   
   create_container('app_ami', 'app_ami', {},{})
   create_container('app_call', 'app_call', {},{})
   create_container('app_db', 'app_db', {},{})
   create_container('app_new_call', 'app_new_call', {},{})
   create_container('app_rcv', 'app_rcv', {},{})
   create_container('app_snd', 'app_snd', {},{})

def start():
   """
   Функция для запуска сервисов.
   """
   # Запуск контейнеров
   start_container('rabbitmq')
   start_container('redis')
   start_container('mariadb')
   start_container('app_ami')
   start_container('app_call')
   start_container('app_db')
   start_container('app_new_call')
   start_container('app_rcv')
   start_container('app_snd')

def stop():
   """
   Функция для остановки сервисов.
   """
   # Остановка контейнеров
   stop_container('rabbitmq')
   stop_container('redis')
   stop_container('mariadb')
   stop_container('app_ami')
   stop_container('app_call')
   stop_container('app_db')
   stop_container('app_new_call')
   stop_container('app_rcv')
   stop_container('app_snd')

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
       