
import os
import tempfile
from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from models import db, Settings

settings_bp = Blueprint('settings_bp', __name__, template_folder='../templates/settings')

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
   """
   Обработчик для отображения и изменения настроек.

   Returns:
       Response: Ответ сервера.
   """
   settings = Settings.query.first()

   if settings is None:
       # Создание новой записи в таблице Settings
       settings = Settings()
       db.session.add(settings)
       db.session.commit()

   if request.method == 'POST':
       # Обработка формы для изменения настроек
       greeting_file = request.files.get('greeting_file')
       modules = request.form.getlist('modules')

       if greeting_file:
           # Сохранение нового файла приветствия
           greeting_file_path = os.path.join(tempfile.gettempdir(), greeting_file.filename)
           greeting_file.save(greeting_file_path)
           settings.greeting_file = greeting_file_path

       # Обработка модулей
       settings.modules = {module: module in modules for module in settings.modules}

       db.session.commit()
       flash('Настройки успешно сохранены!', 'success')
       return redirect(url_for('settings_bp.settings'))

   return render_template('settings.html', settings=settings)



@settings_bp.route('/settings/greeting_file')
@login_required
def get_greeting_file():
    settings = Settings.query.first()
    if settings.greeting_file:
        return send_file(settings.greeting_file, as_attachment=True)
    else:
        abort(404)

@settings_bp.route('/settings/greeting_file/delete', methods=['POST'])
@login_required
def delete_greeting_file():
    settings = Settings.query.first()
    if settings.greeting_file:
        os.remove(settings.greeting_file)
        settings.greeting_file = None
        db.session.commit()
        flash('Файл голосового приветствия успешно удален!', 'success')
    else:
        flash('Файл голосового приветствия не найден.', 'danger')
    return redirect(url_for('settings_bp.settings'))
