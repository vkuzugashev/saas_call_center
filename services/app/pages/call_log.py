from datetime import datetime, timedelta
import logging
import os

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required
import requests

from models import Call, Contact, User

call_log_bp = Blueprint('call_log_bp', __name__, template_folder='../templates/call_log')

# Url для загрузки файла записи
RECORD_URL = os.getenv('RECORD_URL')

logger = logging.getLogger("call_log")

@call_log_bp.route('/calls/log')
@login_required
def show_log():
    """
    Обработчик для отображения журнала вызовов.

    Returns:
       Response: Ответ сервера.
    """
    # Установка значений by default
    date_time_format = '%Y-%m-%d'   # формат DD.MM.YY
    limit = 10
    today = datetime.now().strftime(date_time_format)  # Текущая дата в формате DD.MM.YYYY
    page = int(request.args.get('page', 1))
    fromdt = request.args.get('fromdt', today)
    todt = request.args.get('todt', today)

    # Преобразование строковых значений в объекты datetime
    try:
        from_date = datetime.strptime(fromdt, date_time_format)
        to_date = datetime.strptime(todt, date_time_format) + timedelta(days=1)
       
    except ValueError:
        # Если дата некорректна, возвращаем ошибку
        flash(f'Некорректный формат даты. Должен быть YYYY-MM-DD.')
        return redirect(url_for('call_log_bp.calls_log'))

    # Определяем базовый запрос
    base_query = Call.query.order_by(Call.call_start)

    # Применяем фильтры по дате
    if from_date:
        base_query = base_query.filter(Call.call_start >= from_date)
    if to_date:
        base_query = base_query.filter(Call.call_start <= to_date)
 
    # Извлекаем записи для текущей страницы
    paginate = base_query.paginate(page=page, per_page=limit, error_out=False)

    if paginate.items:
        phones = [item.caller for item in paginate.items]
        phones.extend([item.callee for item in paginate.items])
    else:
        phones = []

    # Получим список контактов
    if phones:
        contacts = { item.phone: item.name for item in Contact.query.filter(Contact.phone.in_(phones)).all()}
        users = { item.phone: item.fio for item in User.query.filter(User.phone.in_(phones)).all()}
        contacts = { **contacts, **users }
    else:
        contacts = {}

    # Формируем контекст для рендеринга
    context = {
       'pagination': paginate,
       'fromdt': fromdt,
       'todt': todt,
       'modules': current_app.config['modules'],
       'contacts': contacts
    }

    return render_template('calls_log.html', **context)


@call_log_bp.route("/record/<int:id>")
@login_required
def get_record_file(id):
   """
   Обработчик для загрузки файла записи звонка.

   Args:
       id (int): Идентификатор звонка.

   Returns:
       Response: Ответ сервера.
   """
   # Получаем звонок
   call = Call.query.get_or_404(id)
   
   if call.record_file:
       file_url = RECORD_URL+'/'+call.record_file
       logger.debug(f'Начало загрузки файла: {file_url}')
       # Загрузка файла по ссылке
       response = requests.get(file_url, stream=True)
   
       # Проверяем успешность загрузки
       if response.status_code == 200:
           # Передача файла клиенту
           filename = os.path.basename(file_url)
           logger.debug(f'Загружен файл: {filename}')
           return send_file(response.raw, download_name=filename, as_attachment=True)
       else:
           return f"Не удалось загрузить файл. Код статуса: {response.status_code}", 500
   else:
       abort(404)

