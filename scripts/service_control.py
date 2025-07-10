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

logging.basicConfig(level='INFO')
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

def get_python_cmd():
   system = platform.system().lower()
   if system == 'windows':
      return 'py'
   elif system == 'linux':
      return 'python3'
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
         logger.info(f"Команда {post_command} успешно запущена.")

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

def remove(service_name):
   """
   Функция для удаления контейнеров и образов Docker для сервиса.
   """
   # Удаление контейнеров
   if service_name == 'all' or service_name == 'asterisk':
      remove_container('asterisk')
   
   if service_name == 'all' or service_name == 'rabbitmq':
      remove_container('rabbitmq')

   if service_name == 'all' or service_name == 'redis':
      remove_container('redis')
   
   if service_name == 'all' or service_name == 'mariadb':
      remove_container('mariadb')
   
   if service_name == 'all' or service_name == 'app_ami':      
      remove_container('app_ami')

   if service_name == 'all' or service_name == 'app_call':
      remove_container('app_call')

   if service_name == 'all' or service_name == 'app_db':
      remove_container('app_db')
   
   if service_name == 'all' or service_name == 'app_new_call':
      remove_container('app_new_call')
   
   if service_name == 'all' or service_name == 'app_rcv':
      remove_container('app_rcv')
   
   if service_name == 'all' or service_name == 'app_snd':
      remove_container('app_snd')
   
   if service_name == 'all' or service_name == 'app':
      remove_container('app')
   
   # Удаление образов
   if service_name == 'all' or service_name == 'asterisk':
      remove_image('asterisk')

   if service_name == 'all' or service_name == 'rabbitmq':
      remove_image('rabbitmq')

   if service_name == 'all' or service_name == 'redis':
      remove_image('redis')

   if service_name == 'all' or service_name == 'mariadb':
      remove_image('mariadb')

   if service_name == 'all' or service_name == 'app_ami':
      remove_image('app_ami')

   if service_name == 'all' or service_name == 'app_call':
      remove_image('app_call')

   if service_name == 'all' or service_name == 'app_db':
      remove_image('app_db')

   if service_name == 'all' or service_name == 'app_new_call':
      remove_image('app_new_call')

   if service_name == 'all' or service_name == 'app_rcv':
      remove_image('app_rcv')

   if service_name == 'all' or service_name == 'app_snd':
      remove_image('app_snd')

   if service_name == 'all' or service_name == 'app':
      remove_image('app')

def build(service_name):
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

   db_name = os.environ.get('DB_NAME')   
   if not db_name:
      db_name = 'call_center'
   new_env_lines['DB_NAME']=db_name   

   db_username = os.environ.get('DB_USERNAME')   
   if not db_username:
      db_username = 'root'
   
   new_env_lines['DB_USERNAME']=db_username   

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

   SPEECH_MODEL = os.environ.get('SPEECH_MODEL', 'general')
   if SPEECH_MODEL:
      new_env_lines['SPEECH_MODEL']=SPEECH_MODEL

   # Зададим значения модулей если уже заданы или по умолчанию
   modules = {}

   MOD_RECORD = os.environ.get('MOD_RECORD', 'false').strip().lower()
   if MOD_RECORD:
      MOD_RECORD = MOD_RECORD == 'true'
      modules['MOD_RECORD'] = MOD_RECORD
      new_env_lines['MOD_RECORD'] = MOD_RECORD

   MOD_NEW_CALL = os.environ.get('MOD_NEW_CALL', 'false').strip().lower()
   if MOD_NEW_CALL:
      MOD_NEW_CALL = MOD_NEW_CALL == 'true'
      modules['MOD_NEW_CALL'] = MOD_NEW_CALL
      new_env_lines['MOD_NEW_CALL'] = MOD_NEW_CALL
   
   MOD_STATISTIC = os.environ.get('MOD_STATISTIC', 'false').strip().lower()
   if MOD_STATISTIC:
      MOD_STATISTIC = MOD_STATISTIC == 'true'
      modules['MOD_STATISTIC'] = MOD_STATISTIC
      new_env_lines['MOD_STATISTIC'] = MOD_STATISTIC
   
   MOD_TRANSCRIPT = os.environ.get('MOD_TRANSCRIPT', 'false').strip().lower()
   if MOD_TRANSCRIPT:
      MOD_TRANSCRIPT = MOD_TRANSCRIPT == 'true'
      modules['MOD_TRANSCRIPT'] = MOD_TRANSCRIPT
      new_env_lines['MOD_TRANSCRIPT'] = MOD_TRANSCRIPT
            
   # Сохранить значения new_env_lines обратно в файл .env
   with open('.env', 'w', encoding='utf-8') as f:
      for key, value in new_env_lines.items():
         key = key.strip().upper()
         f.write(f'{key}={value}\n')

   # Сохранить минимум значений для создания БД
   with open(os.path.join(app_path,'.env'), 'w', encoding='utf-8') as f:
      for key, value in new_env_lines.items():
         if key in ['DB_USERNAME', 'DB_PWD', 'MANAGER_USER', 'MANAGER_PWD']:
            key = key.strip().upper()
            f.write(f'{key}={value}\n')


   # Остановка контейнеров   
   stop(service_name)

   # Удаление контейнеров
   remove(service_name)

   # Создание образов только тех, что требуется
   if service_name == 'all' or service_name == 'asterisk':
      if service_name == 'asterisk':
         # Вызвать скрипт build_users.py для создания пользователей
         py = get_python_cmd()
         command = [py, 'build_users.py']
         result = subprocess.run(command, capture_output=True, text=True)
         if result.returncode != 0:
            raise RuntimeError(f"Ошибка при запуска build_users.py: {result.stderr}")
         else:
            logger.info("Скрипт build_users.py успешно выполнен.")

      # заменим адрес в файле asterisk/conf/pjsip.conf
      with open(os.path.join(asterisk_path,'conf/pjsip.conf'), 'rt') as f:
         lines = f.readlines()
      
      with open(os.path.join(asterisk_path,'conf/pjsip.conf'), 'wt') as f:
         for line in lines:
            # Проверяем строку на наличие IP-адреса
            if '=' in line:
               # Получаем ключ и значение
               key, _ = line.strip().split('=', 1)
               key = key.strip()
               if key in ['external_media_address','external_signaling_address']:
                  # Заменяем значение ключа на local_ip
                  line = f'{key}={local_ip}\n'
            f.write(line)

      # заменим адрес в файле asterisk/conf/users_template.conf
      with open(os.path.join(asterisk_path,'conf/users_template.conf'), 'rt') as f:
         lines = f.readlines()
      
      with open(os.path.join(asterisk_path,'conf/users_template.conf'), 'wt') as f:
         for line in lines:
            # Проверяем строку на наличие IP-адреса
            if '=' in line:
               # Получаем ключ и значение
               key, _ = line.strip().split('=', 1)
               key = key.strip()
               if key in ['media_address']:
                  # Заменяем значение ключа на local_ip
                  line = f'{key}={local_ip}\n'
            f.write(line)

      create_image('asterisk', asterisk_path)
   
   if service_name == 'all' or service_name == 'mariadb':
      with open(os.path.join(mariadb_path,'init.sql'), 'wt') as f:
         # Создаём базу данных
         f.write(f'CREATE DATABASE IF NOT EXISTS {db_name};\r\n')
         # Если нужно создать пользователя и назначить ему привилегии
         f.write(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_username}'@'%' IDENTIFIED BY '{db_password}';\r\n")
         f.write('FLUSH PRIVILEGES;\r\n')
      create_image('mariadb', mariadb_path)
      os.remove(os.path.join(mariadb_path,'init.sql'))
   
   if service_name == 'all' or service_name == 'app':
      create_image('app', app_path)
   
   if modules['MOD_STATISTIC']:
      # Создание образов
      if service_name == 'all' or service_name == 'rabbitmq':
         create_image('rabbitmq', rabbitmq_path)

      if service_name =='all' or service_name == 'redis':
         create_image('redis', redis_path)
      
      if service_name == 'all' or service_name == 'app_ami':
         create_image('app_ami', app_ami_path)

      if service_name == 'all' or service_name == 'app_call':
         create_image('app_call', app_call_path)

      if service_name == 'all' or service_name == 'app_db':
         create_image('app_db', app_db_path)
   
   if modules['MOD_RECORD']:
      None
   
   if modules['MOD_TRANSCRIPT']:
      # Создание образов
      if service_name == 'all' or service_name == 'app_rcv':
         create_image('app_rcv', app_rcv_path)
      
      if service_name == 'all' or service_name == 'app_snd':
         create_image('app_snd', app_snd_path)

   if modules['MOD_NEW_CALL']:
      # Создание образов
      if service_name == 'all' or service_name == 'app_new_call':
         create_image('app_new_call', app_new_call_path)

   if service_name == 'all' or service_name == 'asterisk':
      # Запуск контейнеров если созданы образы
      create_container('asterisk', 'asterisk',{
         'MOD_RECORD': modules['MOD_RECORD'],
      }, {  
         '5060':'5060/udp',
         '5061':'5061/udp',
         '5038':'5038',
         '10000-10100':'10000-10100/udp',
         '8088':'8088',
         '8089':'8089'
      },{
         os.path.join(asterisk_path,'sounds'): '/var/lib/asterisk/sounds',
         '../var/asterisk/monitor':'/var/spool/asterisk/monitor',
         '../var/asterisk/log':'/var/log/asterisk'
      })

   if service_name == 'all' or service_name == 'rabbitmq':
      create_container('rabbitmq', 'rabbitmq', {},{'5672':'5672'})
   
   if service_name == 'all' or service_name == 'redis':
      create_container('redis', 'redis', {}, {'6379': '6379'})

   if service_name == 'all' or service_name == 'mariadb':
      create_container('mariadb', 'mariadb', {       
         'MARIADB_ROOT_PASSWORD': db_password,
         'MARIADB_DATABASE': db_name},
         {'3306': '3306'},
         {
            '../var/mariadb': '/var/lib/mysql'
         })
   
   if service_name == 'all' or service_name == 'app_ami':
      create_container('app_ami', 'app_ami', {
         'ASTERISK_HOST': local_ip,
         'RABBIT_HOST': local_ip,
      },{})
   
   if service_name == 'all' or service_name == 'app_call':
      create_container('app_call', 'app_call', {
         'RABBIT_HOST': local_ip,
         'REDIS_HOST': local_ip
      },{})

   if service_name == 'all' or service_name == 'app_db':
      create_container('app_db', 'app_db', {
         'RABBIT_HOST': local_ip,
         'DB_HOST': local_ip,
         'DB_USERNAME': db_username,
         'DB_PWD': db_password,
      },{})
   
   if service_name == 'all' or service_name == 'app_new_call':
      create_container('app_new_call', 'app_new_call', {
         'DB_HOST': local_ip,
         'DB_NAME': db_name,
         'DB_USERNAME': db_username,
         'DB_PWD': db_password,
         'WEBSOCKET_HOST': '0.0.0.0',
         'RABBIT_HOST': local_ip,
      },{'5078':'5078'})
   
   if service_name == 'all' or service_name == 'app_rcv':
      create_container('app_rcv', 'app_rcv', {
         'DB_HOST': local_ip,
         'DB_NAME': db_name,
         'DB_USERNAME': db_username,
         'DB_PWD': db_password,
         'API_KEY': API_KEY,
         'API_SECRET_KEY': API_SECRET_KEY
      },{})
   
   if service_name == 'all' or service_name == 'app_snd':
      create_container('app_snd', 'app_snd', {
         'DB_HOST': local_ip,
         'DB_NAME': db_name,
         'DB_USERNAME': db_username,
         'DB_PWD': db_password,
         'RECORD_URL_PREFIX': f'http://{local_ip}:8088/static/monitor/',
         'YOS_ACCESS_KEY_ID': YOS_ACCESS_KEY_ID,
         'YOS_SECRET_ACCESS_KEY': YOS_SECRET_ACCESS_KEY,
         'YOS_BUCKET_NAME': YOS_BUCKET_NAME,
         'API_KEY': API_KEY,
         'API_SECRET_KEY': API_SECRET_KEY,
         'SPEECH_MODEL': SPEECH_MODEL
      },{})
   
   if service_name == 'all' or service_name == 'app':
      create_container('app', 'app', {
         'DB_HOST': local_ip,
         'DB_USERNAME': db_username,
         'DB_PWD': db_password,
         'MANAGER_USER': manager_user,
         'MANAGER_PWD': manager_password,
         'RECORD_URL': f'http://{local_ip}:8088/static/monitor',
         'MOD_STATISTIC': modules['MOD_STATISTIC'],
         'MOD_RECORD': modules['MOD_RECORD'],
         'MOD_TRANSCRIPT': modules['MOD_TRANSCRIPT'],
         'MOD_NEW_CALL': modules['MOD_NEW_CALL'],
         'MANAGEMENT_CONSOLE_URL': f'http://{local_ip}:8888'         
      }, {'5000': '5000'})


def start(service_name):
   """
   Функция для запуска сервисных контейнеров.
   """
   # Запуск контейнеров
   if service_name == 'all' or service_name == 'asterisk':
      start_container('asterisk')

   if service_name == 'all' or service_name == 'rabbitmq':
      start_container('rabbitmq')
   
   if service_name == 'all' or service_name == 'redis':
      start_container('redis')
   
   if service_name == 'all' or service_name == 'mariadb':
      start_container('mariadb')   
      # Задержка 10 сек для того чтобы все запустилось
      time.sleep(10)

   if service_name == 'all' or service_name == 'asterisk' or service_name == 'app_ami':
      start_container('app_ami')
   
   if service_name == 'all' or service_name == 'app_call':
      start_container('app_call')

   if service_name == 'all' or service_name == 'app_db':
      start_container('app_db')

   if service_name == 'all' or service_name == 'app':
      py = get_python_cmd()      
      start_container('app', [py, os.path.join(SERVICE_PATH,'app/create_db.py')])
   
   if service_name == 'all' or service_name == 'app_rcv':
      start_container('app_rcv')

   if service_name == 'all' or service_name == 'app_snd':
      start_container('app_snd')

   if service_name == 'all' or service_name == 'app_new_call':
      start_container('app_new_call')

def stop(service_name):
   """
   Функция для остановки сервисных контейнеров.
   """
   # Остановка контейнеров
   if service_name == 'all' or service_name == 'app':
      stop_container('app')

   if service_name == 'all' or service_name == 'app_rcv':
      stop_container('app_rcv')
   
   if service_name == 'all' or service_name == 'app_snd':
      stop_container('app_snd')

   if service_name == 'all' or service_name == 'app_db':      
      stop_container('app_db')
   
   if service_name == 'all' or service_name == 'app_call':
      stop_container('app_call')

   if service_name == 'all' or service_name == 'asterisk' or service_name == 'app_ami':
      stop_container('app_ami')

   if service_name == 'all' or service_name == 'app_new_call':
      stop_container('app_new_call')
   
   if service_name == 'all' or service_name == 'asterisk':
      stop_container('asterisk')

   if service_name == 'all' or service_name == 'rabbitmq':
      stop_container('rabbitmq')
   
   if service_name == 'all' or service_name == 'redis':
      stop_container('redis')

   if service_name == 'all' or service_name == 'mariadb':
      stop_container('mariadb')

def service_status(service_name):
   """
   Функция для получения статуса сервисных контейнеров.
   """
   docker = get_docker_cmd()
   command = [docker, 'ps', '-a', '--format', '{{.Names}}\t{{.Status}}']
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      raise RuntimeError(f"Ошибка при получении статуса сервисов: {result.stderr}")

   for line in result.stdout.splitlines():
      name, status = line.split('\t')
      if service_name == 'all':
         print(f'{name}\t{status}')
      elif name.startswith(service_name):
         print(f'{service_name}\t{status}')
         return
  
   
if __name__ == '__main__':
   if len(sys.argv) < 3:
       logger.info("Использование: py | python3 service_control.py [build|start|stop] service_name")
       sys.exit(1)
   
   command = sys.argv[1]
   service_name = sys.argv[2]
   
   if command == 'build':
       build(service_name)
   elif command == 'start':
       start(service_name)
   elif command == 'stop':
       stop(service_name)
   elif command == 'status':
       service_status(service_name)
   else:
       logger.warning("Недопустимая команда.")
       sys.exit(1)
       