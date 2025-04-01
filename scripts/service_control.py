import os
import platform
import subprocess
import random
import string
import sys
import logging
import socket

from dotenv import load_dotenv

logger = logging.getLogger("service_control")

SERVICE_PATH = '../service/'

load_dotenv()

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

def get_docker_cmd():
   system = platform.system().lower()
   if system == 'windows':
      return 'docker'
   elif system == 'linux':
      return 'podman'
   else:
       raise RuntimeError("Unsupported OS")

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
   docker = get_docker_cmd()
   command = [docker, 'build', '-t', image_name, dockerfile_path]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании образа: {result.stderr}")
   else:
       logger.info(f"Образ {image_name} успешно создан.")

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
   docker = get_docker_cmd()

   try:
       inspect_command = [docker, 'inspect', '--type', 'image', image_name]
       inspect_result = subprocess.run(inspect_command, capture_output=True, text=True)
       if inspect_result.returncode != 0:
           logger.error(f"Образ {image_name} не существует.")
           return
   except Exception as e:
       logger.warning(f"Ошибка при проверке существования образа: {e}")
       return

   env_args = []
   for key, value in env_vars.items():
       env_args.extend(['-e', f'{key}={value}'])

   port_args = []
   for host_port, container_port in ports.items():
       port_args.extend(['-p', f'{host_port}:{container_port}'])

   # Создание контейнера
   command = [docker, 'create', '--name', container_name] + env_args + port_args + [image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании контейнера: {result.stderr}")
   else:
       logger.info(f"Контейнер {container_name} успешно создан.")

def remove_container(container_name):
   """
   Функция для удаления Docker контейнера.

   Args:
      container_name (str): Имя контейнера.

   Returns:
      None
   """
   # Проверяем наличие контейнера
   docker = get_docker_cmd()
   try:
       inspect_command = [docker, 'inspect', '--type','container', container_name]
       inspect_result = subprocess.run(inspect_command, capture_output=True, text=True)
       if inspect_result.returncode != 0:
           logger.error(f"Контейнер {container_name} не существует.")
           return
   except Exception as e:
       logger.warning(f"Ошибка при проверке существования контейнера: {e}")
       return

   # Удаление контейнера
   command = [docker, 'rm', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при удалении контейнера: {result.stderr}")
   else:
       logger.info(f"Контейнер {container_name} успешно удален.")

def remove_image(image_name):
   """
   Функция для удаления Docker образа.

   Args:
      container_name (str): Имя образа.

   Returns:
      None
   """
   # Проверяем наличие образа
   docker = get_docker_cmd()
   
   try:
       inspect_command = [docker, 'inspect', '--type', 'image', image_name]
       inspect_result = subprocess.run(inspect_command, capture_output=True, text=True)
       if inspect_result.returncode != 0:
           logger.error(f"Образ {image_name} не существует.")
           return
   except Exception as e:
       logger.warning(f"Ошибка при проверке существования образа: {e}")
       return

   # Удаление образа
   command = [docker, 'image', 'rm', image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при удалении образа: {result.stderr}")
   else:
       logger.info(f"Образ {image_name} успешно удален.")

def start_container(container_name):
   """
   Функция для запуска Docker контейнера.

   Args:
       container_name (str): Имя контейнера.

   Returns:
       None
   """
   docker = get_docker_cmd()

   try:
       inspect_command = [docker, 'inspect', '--type', 'container', container_name]
       inspect_result = subprocess.run(inspect_command, capture_output=True, text=True)
       if inspect_result.returncode != 0:
           logger.error(f"Контейнер {container_name} не существует.")
           return
   except Exception as e:
       logger.warning(f"Ошибка при проверке существования контейнера: {e}")
       return
     
   command = [docker, 'start', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при запуске контейнера: {result.stderr}")
   else:
       logger.info(f"Контейнер {container_name} успешно запущен.")

def stop_container(container_name):
   """
   Функция для остановки Docker контейнера.

   Args:
       container_name (str): Имя контейнера.

   Returns:
       None
   """
   # Проверяем наличие контейнера
   docker = get_docker_cmd()
   try:
       inspect_command = [docker, 'inspect', '--type', 'container', container_name]
       inspect_result = subprocess.run(inspect_command, capture_output=True, text=True)
       if inspect_result.returncode != 0:
           logger.error(f"Контейнер {container_name} не существует.")
           return
   except Exception as e:
       logger.warning(f"Ошибка при проверке существования контейнера: {e}")
       return

   # Остановка контейнера
   command = [docker, 'stop', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при остановке контейнера: {result.stderr}")
   else:
       logger.info(f"Контейнер {container_name} успешно остановлен.")

def remove():
   """
   Функция для удаления сервисов.
   """
   # Удаление контейнеров
   remove_container('asterisk')
   remove_container('rabbitmq')
   remove_container('redis')
   remove_container('mariadb')
   remove_container('app_ami')
   remove_container('app_call')
   remove_container('app_call')
   remove_container('app_db')
   remove_container('app_new_call')
   remove_container('app_rcv')
   remove_container('app_snd')
   remove_container('app')
   
   # Удаление образов
   remove_image('asterisk')
   remove_image('rabbitmq')
   remove_image('redis')
   remove_image('mariadb')
   remove_image('app_ami')
   remove_image('app_call')
   remove_image('app_db')
   remove_image('app_new_call')
   remove_image('app_rcv')
   remove_image('app_snd')
   remove_image('app')

def build():
   """
   Функция для создания сервисов.
   """
   asterisk_path = os.path.join(SERVICE_PATH, 'asterisk')
   rabbitmq_path = os.path.join(SERVICE_PATH, 'rabbitmq')
   redis_path = os.path.join(SERVICE_PATH, 'redis')
   mariadb_path = os.path.join(SERVICE_PATH, 'mariadb')
   app_ami_path = os.path.join(SERVICE_PATH, 'app_ami')
   app_call_path = os.path.join(SERVICE_PATH, 'app_call')
   app_db_path = os.path.join(SERVICE_PATH, 'app_db')
   app_new_call_path = os.path.join(SERVICE_PATH, 'app_new_call')
   app_rcv_path = os.path.join(SERVICE_PATH, 'app_rcv_trns')
   app_snd_path = os.path.join(SERVICE_PATH, 'app_snd_trns')
   app_path = os.path.join(SERVICE_PATH, 'app')
   
   # Получаем локальный IP-адрес
   local_ip = get_local_ip()
      
   # Получаем пароль от БД
   db_password = os.environ.get('MARIADB_ROOT_PASSWORD')
   if not db_password:
      # Генерация пароля для root пользователя БД
      db_password = generate_password()
      # Запись пароля в .env файл
      with open('.env', 'a') as f:
         f.write(f'MARIADB_ROOT_PASSWORD={db_password}\n')   

   # Получить пароль для пользователя admin для сайта
   manager_password = os.environ.get('MANAGER_PWD')
   if not manager_password:
      # Генерация пароля для пользователя admin
      manager_password = generate_password()
      # Запись пароля в .env файл
      with open('.env', 'a') as f:
         f.write(f'MANAGER_PWD={manager_password}\n')   

   # Создаем словарь с модулями
   modules = {'mod_statistic': False, 'mod_transcript': False, 'mod_record': False, 'mod_new_call': False}
   # Остановка контейнеров   
   stop()
   # Удаление образов
   remove()

   # Создание образов только тех, что требуется
   create_image('asterisk', asterisk_path)
   create_image('mariadb', mariadb_path)
   create_image('app', app_path)
   
   if modules['mod_statistic']:       
      # Создание образов
      create_image('rabbitmq', rabbitmq_path)
      create_image('redis', redis_path)
      create_image('app_ami', app_ami_path)
      create_image('app_call', app_call_path)
      create_image('app_db', app_db_path)
   
   if modules['mod_record']:
      None
   
   if modules['mod_transcript']:
      # Создание образов
      create_image('app_rcv', app_rcv_path)
      create_image('app_snd', app_snd_path)

   if modules['mod_new_call']:
      # Создание образов
      create_image('app_new_call', app_new_call_path)

   # Запуск контейнеров если созданы образы
   create_container('asterisk', 'asterisk',{}, {  
      '5060':'5060/udp',
      '5038':'5038',
      '10000-10100':'10000-10100/udp',
      '8088':'8088'
   })
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
   create_container('app', 'app', {
      'DB_HOST': local_ip,
      'DB_PASSWORD': db_password,
      'MANAGER_USER': 'admin',
      'MANAGER_PWD': manager_password,
      'RECORD_URL': f'http://{local_ip}:8088/static/monitor'
   }, {'5000': '5000'})

def start():
   """
   Функция для запуска сервисов.
   """
   # Запуск контейнеров
   start_container('asterisk')
   start_container('rabbitmq')
   start_container('redis')
   start_container('mariadb')
   start_container('app_ami')
   start_container('app_call')
   start_container('app_db')
   start_container('app_new_call')
   start_container('app_rcv')
   start_container('app_snd')
   start_container('app')

def stop():
   """
   Функция для остановки сервисов.
   """
   # Остановка контейнеров
   stop_container('asterisk')
   stop_container('rabbitmq')
   stop_container('redis')
   stop_container('mariadb')
   stop_container('app_ami')
   stop_container('app_call')
   stop_container('app_db')
   stop_container('app_new_call')
   stop_container('app_rcv')
   stop_container('app_snd')
   stop_container('app')


if __name__ == '__main__':
   if len(sys.argv) != 2:
       logger.info("Использование: py | python3 service_control.py [build|start|stop]")
       sys.exit(1)
   
   command = sys.argv[1]
   
   if command == 'build':
       build()
   elif command == 'start':
       start()
   elif command == 'stop':
       stop()
   else:
       logger.warning("Недопустимая команда.")
       sys.exit(1)
       