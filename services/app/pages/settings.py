
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
   service_statuses = {}

   response = requests.get(f'{url}/service/status/all')
   if response.status_code == 200:
      service_statuses = json.loads(response.text)

   context = {
      'modules':  current_app.config['modules'],
      'services': service_statuses
   }
   return render_template('settings.html', **context)
