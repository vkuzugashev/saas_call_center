import os
from flask import Flask, request, jsonify
import subprocess
import psutil

app = Flask(__name__)

SCRIPT_PATH = os.path.abspath('../../scripts')
PYTHON_CMD = 'py'
SERVICE_CONTROL_SCRIPT = 'service_control.py'

@app.route('/service/build/<service_name>', methods=['GET','POST'])
def build_service(service_name):
   os.chdir(SCRIPT_PATH)
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'build', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} built', 'error': result.stderr})
   else:
      return jsonify({'message': f'Service {service_name} built'})

@app.route('/service/stop/<service_name>', methods=['GET','POST'])
def stop_service(service_name):
   os.chdir(SCRIPT_PATH)
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'stop', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} stop', 'error': result.stderr})
   else:
      return jsonify({'message': f'Service {service_name} stopped'})

@app.route('/service/start/<service_name>', methods=['GET','POST'])
def start_service(service_name):
   os.chdir(SCRIPT_PATH)
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'start', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} start', 'error': result.stderr})
   else:
      return jsonify({'message': f'Service {service_name} started'})


@app.route('/service/status/<service_name>', methods=['GET'])
def get_service_status(service_name):
   os.chdir(SCRIPT_PATH)
   command = [PYTHON_CMD, SERVICE_CONTROL_SCRIPT, 'status', service_name]
   result = subprocess.run(command, capture_output=True, text=True)
   if result.returncode != 0:
      return jsonify({'message': f'Failt service {service_name} status', 'error': result.stderr.strip()})
   else:
      return jsonify({'message': f'Service {service_name} status', 'status': result.stdout.strip()})


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8888, debug=True)
