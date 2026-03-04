import logging
import os
from datetime import datetime, timedelta
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required
import requests
from sqlalchemy import and_, func
from models.model import get_db, User, Call, Contact
from .paginate import Pagination

call_log_bp = Blueprint('call_log_bp', __name__, template_folder='../templates/call_log')

logger = logging.getLogger("call_log")

# Url для загрузки файла записи
RECORD_URL = os.getenv('ASTERISK_RECORD_URL')

def get_session():
    return next(get_db())

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

    with get_session() as session:
        # Определяем базовый запрос
        stmt = session.query(Call).order_by(Call.call_start)
        
        # Применяем фильтры по дате
        stmt = stmt.filter(and_(Call.call_start >= from_date, Call.call_start < to_date))
    
        # Подсчёт общего количества записей
        total_stmt = session.query(func.count('*')).select_from(Call).filter(*stmt.whereclause)
        total = session.execute(total_stmt).scalar()

        # Выборка данных для страницы
        items = stmt.offset((page - 1) * limit).limit(limit).all()

        paginate = Pagination(items, page, limit, total)

        if paginate.items:
            phones = [item.caller for item in paginate.items]
            phones.extend([item.callee for item in paginate.items])
        else:
            phones = []

        # Получим список контактов
        if phones:
            contacts = { item.phone: item.name for item in session.query(Contact).filter(Contact.phone.in_(phones)).all()}
            users = { item.phone: item.fio for item in session.query(User).filter(User.phone.in_(phones)).all()}
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
    with get_session() as session:
        # Получаем звонок
        call = session.get(Call, id)
        if call and call.record_file:
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

