
import json
import os
from flask import Blueprint, render_template, current_app
from flask_login import login_required
import requests

settings_bp = Blueprint('settings_bp', __name__, template_folder='../templates/settings')

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
   """
   Обработчик для отображения и изменения настроек.

   Returns:
       Response: Ответ сервера.
   """
   url = current_app.config['MANAGEMENT_CONSOLE_URL']
   services = ['asterisk', 'app', 'app_ami','app_call', 'app_db', 'app_snd_trns', 'app_rcv_trns', 'app_new_call', 'mariadb', 'redis', 'rabbitmq']  # замените на список ваших сервисов
   service_statuses = {}
   for service in services:
      response = requests.get(f'{url}/service/status/{service}')
      if response.status_code == 200:
         if 'status' in response.text:
            service_statuses[service] = json.loads(response.text)['status']
         else:
            service_statuses[service] = 'Unknown'
   
   context = {
      'modules':  current_app.config['modules'],
      'services': service_statuses
   }
   return render_template('settings.html', **context)
