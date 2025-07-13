import logging
import os
import platform
import threading
import time
import signal
import sys
from flask import Flask, jsonify
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
SCRIPT_PATH = os.path.abspath(os.getenv("SCRIPT_PATH", '../../scripts'))
SERVICE_CONTROL_SCRIPT = os.getenv("SERVICE_CONTROL_SCRIPT", 'service_control.py')
SERVICE_MONITOR_INTERVAL = float(os.getenv("SERVICE_MONITOR_INTERVAL", "60"))

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

monitoring_canceled = False
monitoring_thread = None

def get_python_cmd():
   """
   Функция для получения команды Python.

   Returns:
       str: Команда Python.
   """
   system = platform.system().lower()
   if system == 'windows':
      return 'py'
   elif system == 'linux':
      return 'python3'
   else:
       raise RuntimeError("Unsupported OS")

@app.route('/service/build/<service_name>', methods=['GET','POST'])
def build_service(service_name):
   """
   Обработчик для сборки сервиса.

   Args:
       service_name (str): Имя сервиса.

   Returns:
       Response: Ответ сервера.
   """
   os.chdir(SCRIPT_PATH)
   PYTHON_CMD = get_python_cmd()
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'build', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} built', 'error': result.stderr}), 500
   else:
      return jsonify({'message': f'Service {service_name} built'}), 200

@app.route('/service/stop/<service_name>', methods=['GET','POST'])
def stop_service(service_name):
   """
   Обработчик для остановки сервиса.

   Args:
       service_name (str): Имя сервиса.

   Returns:
       Response: Ответ сервера.
   """
   os.chdir(SCRIPT_PATH)
   PYTHON_CMD = get_python_cmd()
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'stop', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} stop', 'error': result.stderr})
   else:
      return jsonify({'message': f'Service {service_name} stopped'})

@app.route('/service/start/<service_name>', methods=['GET','POST'])
def start_service(service_name):
   """
   Обработчик для запуска сервиса.

   Args:
       service_name (str): Имя сервиса.

   Returns:
       Response: Ответ сервера.
   """
   os.chdir(SCRIPT_PATH)
   PYTHON_CMD = get_python_cmd()
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'start', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} start', 'error': result.stderr}), 500
   else:
      return jsonify({'message': f'Service {service_name} started'}), 200

@app.route('/service/status/<service_name>', methods=['GET'])
def get_service_status(service_name):
   """
   Обработчик для получения статуса сервиса.

   Args:
       service_name (str): Имя сервиса.

   Returns:
       Response: Ответ сервера.
   """
   os.chdir(SCRIPT_PATH)
   PYTHON_CMD = get_python_cmd()
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'status', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} status', 'error': result.stderr.strip()})
   
   services = {}

   for line in result.stdout.splitlines():
      name, status = line.split('\t')
      services[name] = status
         
   return jsonify(services)

def check_services():
   """
   Функция для проверки статуса сервисов и запуска сервисов, которые не работают.
   """
   logger.debug('Checking services...')
   try:
      os.chdir(SCRIPT_PATH)
      PYTHON_CMD = get_python_cmd()
      command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'status', 'all']
      result = subprocess.run(command, capture_output=True, text=True)
      if result.returncode != 0:
         logger.error('Failt service status', result.stderr.strip())
   
      services = {}

      for line in result.stdout.splitlines():
         name, status = line.split('\t')
         services[name] = status

      for service, status in services.items():
         if status.startswith('Exited'):
            command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'start', service]
            logger.info(f'Starting service: {service}')
            subprocess.run(command, capture_output=True, text=True)

   except Exception as e:
      logger.error(f'Error checking services: {e}')

   logger.debug('Finished checking services')

def run_check_services():
   """
   Функция для запуска проверки статуса сервисов каждые 15 секунд.
   """
   # Выполняем цикл пока не получим системный сигнал завершения

   while not monitoring_canceled:
      try:
         # вывести в лог id процесса
         logger.debug(f'Starting process ID: {os.getpid()}')
         check_services()
         logger.debug(f'Stopped process ID: {os.getpid()}')
         time.sleep(SERVICE_MONITOR_INTERVAL)  # Измените интервал на 60 секунд
      except Exception as e:
         logger.error(f'Error in run_check_services: {e}')

def signal_handler(sig, frame):
   logger.info(f'Caught signal {sig}')
   # завершить потоки и завершить программу
   global monitoring_canceled, monitoring_thread
   monitoring_canceled = True
   monitoring_thread.join()
   sys.exit(0)

def monitoring_init():
   signal.signal(signal.SIGINT, signal_handler)
   signal.signal(signal.SIGTERM, signal_handler)
   global monitoring_thread
   monitoring_thread = threading.Thread(target=run_check_services)
   monitoring_thread.start()

if __name__ == '__main__':   
   monitoring_init()
   app.run(host='0.0.0.0', port=8888, debug=True, use_reloader=False)
