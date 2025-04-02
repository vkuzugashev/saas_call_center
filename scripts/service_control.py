import time
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

SERVICE_PATH = '../services/'

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
       raise RuntimeError(f"Ошибка при создании образа {image_name}: {result.stderr}")
   else:
       logger.info(f"Образ {image_name} успешно создан.")

def create_container(container_name, image_name, env_vars, ports, vol_vars={}):
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
       logger.warning(f"Ошибка при проверке существования образа {image_name}: {e}")
       return

   env_args = []
   for key, value in env_vars.items():
       env_args.extend(['-e', f'{key}={value}'])

   port_args = []
   for host_port, container_port in ports.items():
       port_args.extend(['-p', f'{host_port}:{container_port}'])

   vol_args = []
   for host_volume, container_volume in vol_vars.items():
       host_volume = os.path.abspath(host_volume)
       vol_args.extend(['-v', f'{host_volume}:{container_volume}'])

   # Создание контейнера
   command = [docker, 'create', '--name', container_name] + env_args + port_args + vol_args + [image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при создании контейнера {container_name}: {result.stderr}")
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
       logger.warning(f"Ошибка при проверке существования контейнера {container_name}: {e}")
       return

   # Удаление контейнера
   command = [docker, 'rm', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при удалении контейнера {container_name}: {result.stderr}")
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
       logger.warning(f"Ошибка при проверке существования образа {image_name}: {e}")
       return

   # Удаление образа
   command = [docker, 'image', 'rm', image_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при удалении образа {image_name}: {result.stderr}")
   else:
       logger.info(f"Образ {image_name} успешно удален.")

def start_container(container_name, post_command = None):
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
       logger.warning(f"Ошибка при проверке существования контейнера {container_name}: {e}")
       return
     
   command = [docker, 'start', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при запуске контейнера {container_name}: {result.stderr}")
   else:
       logger.info(f"Контейнер {container_name} успешно запущен.")
   
   if post_command:
      result = subprocess.run(post_command, capture_output=True, text=True)
      if result.returncode != 0:
         raise RuntimeError(f"Ошибка при запуске post command {post_command}: {result.stderr}")
      else:
         logger.info(f"Команжа {post_command} успешно запущенв.")

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
       logger.warning(f"Ошибка при проверке существования контейнера {container_name}: {e}")
       return

   # Остановка контейнера
   command = [docker, 'stop', container_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
       raise RuntimeError(f"Ошибка при остановке контейнера {container_name}: {result.stderr}")
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
      
   new_env_lines = {}

   # Получаем пароль от БД
   db_password = os.environ.get('DB_PWD')
   if not db_password:
      # Генерация пароля для root пользователя БД
      db_password = generate_password()
      new_env_lines['DB_PWD']=db_password   

   manager_user = os.environ.get('MANAGER_USER')
   if not manager_user:
      # Генерация пароля для пользователя admin
      manager_user = 'admin'
      new_env_lines['MANAGER_USER']=manager_user   

   # Получить пароль для пользователя admin для сайта
   manager_password = os.environ.get('MANAGER_PWD')
   if not manager_password:
      # Генерация пароля для пользователя admin
      manager_password = generate_password()
      new_env_lines['MANAGER_PWD']=manager_password   

   # YOS
   YOS_ACCESS_KEY_ID = os.environ.get('YOS_ACCESS_KEY_ID')
   if YOS_ACCESS_KEY_ID:
      new_env_lines['YOS_ACCESS_KEY_ID']=YOS_ACCESS_KEY_ID

   YOS_SECRET_ACCESS_KEY = os.environ.get('YOS_SECRET_ACCESS_KEY')
   if YOS_SECRET_ACCESS_KEY:
      new_env_lines['YOS_SECRET_ACCESS_KEY']=YOS_SECRET_ACCESS_KEY

   YOS_BUCKET_NAME = os.environ.get('YOS_BUCKET_NAME')
   if YOS_BUCKET_NAME:
       new_env_lines['YOS_BUCKET_NAME']=YOS_BUCKET_NAME
   
   # SPEECH
   API_KEY = os.environ.get('API_KEY')
   if API_KEY:
       new_env_lines['API_KEY']=API_KEY
   
   API_SECRET_KEY = os.environ.get('API_SECRET_KEY')
   if API_SECRET_KEY:
       new_env_lines['API_SECRET_KEY']=API_SECRET_KEY

   SPEECH_MODEL = os.environ.get('SPEECH_MODEL')
   if SPEECH_MODEL:
      new_env_lines['SPEECH_MODEL']=SPEECH_MODEL

   # Создаем словарь с модулями
   modules = {'MOD_STATISTIC': False, 'MOD_TRANSCRIPT': False, 'MOD_RECORD': False, 'MOD_NEW_CALL': False}
   # копируем modules его в new_env_lines
   new_env_lines.update(modules)

   # Взять значения модулей из файла .env
   with open('.env', 'r', encoding='utf-8') as f:
      env_lines = f.readlines()
      
      for line in env_lines:
         if line.strip() != '' and not line.startswith('#'):
            key, value = line.strip().split('=')
            # Удалим пробелы в ключах и значениях
            key = key.strip().upper()
            key_value = value.strip().lower()
            if key == 'MOD_STATISTIC':
               modules[key] = key_value == 'true'
               new_env_lines[key] = key_value == 'true'
            elif key == 'MOD_TRANSCRIPT':
               modules[key] = key_value == 'true'
               new_env_lines[key] = key_value == 'true'
            elif key == 'MOD_RECORD':
               modules[key] = key_value == 'true'
               new_env_lines[key] = key_value == 'true'
            elif key == 'MOD_NEW_CALL':
               modules[key] = key_value == 'true'
               new_env_lines[key] = key_value == 'true'
            else:
               new_env_lines[key] = value
             
   # Сохранить значения new_env_lines обратно в файл .env
   with open('.env', 'w', encoding='utf-8') as f:
      for key, value in new_env_lines.items():
         key = key.strip().upper()
         f.write(f'{key}={value}\n')

   # Остановка контейнеров   
   stop()
   # Удаление образов
   remove()

   # Создание образов только тех, что требуется
   create_image('asterisk', asterisk_path)
   create_image('mariadb', mariadb_path)
   create_image('app', app_path)
   
   if modules['MOD_STATISTIC']:       
      # Создание образов
      create_image('rabbitmq', rabbitmq_path)
      create_image('redis', redis_path)
      create_image('app_ami', app_ami_path)
      create_image('app_call', app_call_path)
      create_image('app_db', app_db_path)
   
   if modules['MOD_RECORD']:
      None
   
   if modules['MOD_TRANSCRIPT']:
      # Создание образов
      create_image('app_rcv', app_rcv_path)
      create_image('app_snd', app_snd_path)

   if modules['MOD_NEW_CALL']:
      # Создание образов
      create_image('app_new_call', app_new_call_path)

   # Запуск контейнеров если созданы образы
   create_container('asterisk', 'asterisk',{}, {  
      '5060':'5060/udp',
      '5038':'5038',
      '10000-10100':'10000-10100/udp',
      '8088':'8088'
   },{
       os.path.join(asterisk_path,'sounds'): '/var/lib/asterisk/sounds',
       '../var/asterisk/monitor':'/var/spool/asterisk/monitor',
       '../var/asterisk/log':'/var/log/asterisk'
   })
   create_container('rabbitmq', 'rabbitmq', {},{'5672':'5672'})
   create_container('redis', 'redis', {}, {'6379': '6379'})
   create_container('mariadb', 'mariadb', {       
      'MARIADB_ROOT_PASSWORD': db_password,
      'MARIADB_DATABASE': 'call_center'},
      {'3306': '3306'},
      {
         '../var/mariadb': '/var/lib/mysql'
      })   
   create_container('app_ami', 'app_ami', {
       'ASTERISK_HOST': local_ip,
       'RABBIT_HOST': local_ip,
   },{})
   create_container('app_call', 'app_call', {
        'RABBIT_HOST': local_ip,
        'REDIS_HOST': local_ip
   },{})
   create_container('app_db', 'app_db', {
       'RABBIT_HOST': local_ip,
       'DB_HOST': local_ip,
       'DB_PWD': db_password,
   },{})
   create_container('app_new_call', 'app_new_call', {},{})
   create_container('app_rcv', 'app_rcv', {
       'DB_HOST': local_ip,
       'DB_PWD': db_password,
       'API_KEY': API_KEY,
       'API_SECRET_KEY': API_SECRET_KEY
   },{})
   create_container('app_snd', 'app_snd', {
       'DB_HOST': local_ip,
       'DB_PWD': db_password,
       'RECORD_URL_PREFIX': f'http://{local_ip}:8088/static/monitor/',
       'YOS_ACCESS_KEY_ID': YOS_ACCESS_KEY_ID,
       'YOS_SECRET_ACCESS_KEY': YOS_SECRET_ACCESS_KEY,
       'YOS_BUCKET_NAME': YOS_BUCKET_NAME,
       'API_KEY': API_KEY,
       'API_SECRET_KEY': API_SECRET_KEY,
       'SPEECH_MODEL': SPEECH_MODEL
   },{})
   create_container('app', 'app', {
      'DB_HOST': local_ip,
      'DB_PWD': db_password,
      'MANAGER_USER': manager_user,
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
   # Задержка 10 сек для того чтобы все запустилось
   time.sleep(10)

   start_container('app_ami')
   start_container('app_call')
   start_container('app_db')
   start_container('app', ['python', os.path.join(SERVICE_PATH,'app/create_db.py')])
   start_container('app_rcv')
   start_container('app_snd')
   start_container('app_new_call')

def stop():
   """
   Функция для остановки сервисов.
   """
   # Остановка контейнеров
   stop_container('app')
   stop_container('app_rcv')
   stop_container('app_snd')
   stop_container('app_db')
   stop_container('app_call')
   stop_container('app_ami')
   stop_container('app_new_call')
   stop_container('asterisk')
   stop_container('rabbitmq')
   stop_container('redis')
   stop_container('mariadb')

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
       