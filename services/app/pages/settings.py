
import os
from flask import Blueprint, render_template, current_app
from flask_login import login_required

settings_bp = Blueprint('settings_bp', __name__, template_folder='../templates/settings')

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
   """
   Обработчик для отображения и изменения настроек.

   Returns:
       Response: Ответ сервера.
   """
   return render_template('settings.html', modules = current_app.config['modules'])
