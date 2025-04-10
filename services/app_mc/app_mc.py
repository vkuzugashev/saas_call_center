from flask import Flask, request, jsonify
import subprocess
import psutil

app = Flask(__name__)

@app.route('/service/<service_name>/build', methods=['POST'])
def build_service(service_name):
    subprocess.run(['sudo', 'service', service_name, 'build'])
    return jsonify({'message': f'Service {service_name} built'})

@app.route('/service/<service_name>/stop', methods=['POST'])
def stop_service(service_name):
    subprocess.run(['sudo', 'service', service_name, 'stop'])
    return jsonify({'message': f'Service {service_name} stopped'})

@app.route('/service/<service_name>/start', methods=['POST'])
def start_service(service_name):
    subprocess.run(['sudo', 'service', service_name, 'start'])
    return jsonify({'message': f'Service {service_name} started'})

@app.route('/service/<service_name>/status', methods=['GET'])
def get_service_status(service_name):
    service = psutil.Service(service_name)
    return jsonify({'status': service.status})

if __name__ == '__main__':
    app.run(debug=True)
