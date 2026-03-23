import csv
from datetime import datetime
from io import StringIO
import logging
import os
import tempfile
from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from models.model import PJSIPAor, PJSIPAuth, PJSIPEndpoint, get_db, User

extens_bp = Blueprint('extens_bp', __name__, template_folder='../templates/extens')

logger = logging.getLogger("extens")

def get_session():
    return next(get_db())

@extens_bp.route('/extens')
@login_required
def show_extens():
    """
    Обработчик для отображения списка абонентов.

    Returns:
        Response: Ответ сервера.
    """
    with get_session() as session:
        departments = session.query(PJSIPEndpoint.department).distinct().all()

        selected_department = request.args.get('department')

        if selected_department:
            extens = session.query(PJSIPEndpoint, PJSIPAuth.username).join(PJSIPAuth).filter(PJSIPEndpoint.department == selected_department).all()
        else:
            extens = session.query(PJSIPEndpoint, PJSIPAuth.username).join(PJSIPAuth).all()

        return render_template('extens.html',
                                extens=extens,
                                departments=departments,
                                selected_department=selected_department,
                                modules = current_app.config['modules'])


@extens_bp.route('/extens/new', methods=['GET', 'POST'])
@login_required
def create_exten():
    """Создать новый SIP endpoint."""
    with get_session() as session:
        # Получаем список отделов для подсказок
        departments = session.query(PJSIPEndpoint.department).distinct().all()

        if request.method == 'POST':
            ep_id = request.form['id'].strip()
            department = request.form['department'].strip()
            fio = request.form['fio'].strip()
            password = request.form['password']
            username = request.form['username']

            # Проверка на пустые поля
            if not all([ep_id, department, fio, username, password]):
                flash('Все поля обязательны.', 'danger')
                return render_template('extens/exten_create.html', departments=departments, modules=current_app.config['modules'])

            # Проверка на дубликат
            exists = session.get(PJSIPEndpoint, ep_id)
            if exists:
                flash(f'Абонент с ID={ep_id} уже существует.', 'danger')
                return redirect(url_for('extens_bp.show_extens'))

            # Создаём AOR и Auth
            aor = PJSIPAor(id=ep_id)

            auth_obj = PJSIPAuth(
                id=ep_id,
                username=username,
                auth_type='md5'
            )
            
            # Генерируем md5_cred: username:realm:password
            if password:
                auth_obj.set_password(password)

            # Основной endpoint
            endpoint = PJSIPEndpoint(
                id=ep_id,
                department=department,
                fio=fio,
                aors=ep_id,
                auth=ep_id
            )

            try:
                session.add_all([aor, auth_obj, endpoint])
                session.commit()
                flash(f'Абонент {ep_id} успешно создан!', 'success')
                return redirect(url_for('extens_bp.show_extens'))
            except Exception as e:
                session.rollback()
                flash(f'Ошибка при создании: {e}', 'danger')

        # Передаём departments в шаблон
        return render_template(
            'extens/exten_create.html',
            departments=departments,
            modules=current_app.config['modules']
        )


@extens_bp.route('/extens/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_exten(id):
    """Редактировать SIP endpoint."""
    with get_session() as session:
        ep = session.get(PJSIPEndpoint, id)
        if not ep:
            flash('Абонент не найден.', 'danger')
            return redirect(url_for('extens_bp.show_extens'))

        # Получаем список отделов для выпадающего списка
        departments = session.query(PJSIPEndpoint.department).distinct().all()
        
        # Получаем username из Auth
        auth = session.get(PJSIPAuth, ep.auth)
        username = auth.username if auth else ''

        if request.method == 'POST':
            ep.department = request.form['department']
            ep.fio = request.form['fio']
            ep.aors = id
            ep.auth = id

            # Обновим AOR
            aor = session.get(PJSIPAor, ep.aors) or PJSIPAor(id=ep.aors)

            # Обновим Auth
            auth = session.get(PJSIPAuth, ep.auth) or PJSIPAuth(id=ep.auth)
            auth.username = request.form['username'].strip()

            password = request.form['password'].strip()
            if password:
                auth.set_password(password)

            try:
                session.add_all([ep, aor, auth])
                session.commit()
                flash(f'Абонент {id} обновлён.', 'success')
                return redirect(url_for('extens_bp.show_extens'))
            except Exception as e:
                session.rollback()
                flash(f'Ошибка: {e}', 'danger')

        # Передаём departments в шаблон
        return render_template(
            'extens/exten_edit.html',
            ep=ep,
            departments=departments,
            username=username,
            modules=current_app.config['modules']
        )


@extens_bp.route('/extens/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_exten(id):
    """Удалить SIP endpoint и связанные AOR/Auth."""
    with get_session() as session:
        ep = session.get(PJSIPEndpoint, id)
        if not ep:
            flash('Абонент не найден.', 'danger')
            return redirect(url_for('extens_bp.show_extens'))
        
        if request.method == 'POST':
            try:
                # Удаляем связанные записи
                session.query(PJSIPAor).filter(PJSIPAor.id == ep.aors).delete()
                session.query(PJSIPAuth).filter(PJSIPAuth.id == ep.auth).delete()
                session.delete(ep)
                session.commit()
                flash(f'Абонент {id} удалён.', 'success')
            except Exception as e:
                session.rollback()
                flash(f'Ошибка при удалении: {e}', 'danger')

            return redirect(url_for('extens_bp.show_extens'))
        
        return render_template(
            'extens/exten_delete_confirm.html',
            exten=ep,
            modules=current_app.config['modules']
            )


@extens_bp.route('/extens/export_csv')
@login_required
def extens_export_csv():
    """
    Обработчик для экспорта абонентов в CSV-файл.

    Returns:
        Response: Ответ сервера.
    """   
    with get_session() as session:
        # Получаем всех пользователей
        eps = session.query(PJSIPEndpoint, PJSIPAuth.username).join(PJSIPAuth).all()
        
        # Создаем строку для хранения CSV-данных
        si = StringIO()
        cw = csv.writer(si)
        
        # Заголовки столбцов
        cw.writerow(['Номер', 'Отдел', 'Логин', 'ФИО', 'Очередь', 'Пароль'])
        
        # Заполняем строки данными
        for ep, username in eps:
            cw.writerow([ep.id, ep.department, username, ep.fio, None, None])
        
        # Преобразуем содержимое StringIO в байты
        output = make_response(si.getvalue())
        
        # Устанавливаем заголовок Content-Disposition для скачивания файла
        output.headers["Content-Disposition"] = "attachment; filename=extens.csv"
        output.headers["Content-type"] = "text/csv"
        
        return output

@extens_bp.route('/extens/upload_csv', methods=['GET', 'POST'])
@login_required
def extens_upload_csv():
    """
    Обработчик для загрузки абонентов из CSV-файла.

    Returns:
        Response: Ответ сервера.
    """
    if request.method == 'POST':
        # Проверяем, есть ли файл в запросе
        if 'file' not in request.files:
            flash('Нет файла для загрузки', 'warning')
            return redirect(request.url)
        
        file = request.files['file']

        # Если пользователь не выбрал файл
        if file.filename == '':
            flash('Не выбран файл', 'warning')
            return redirect(request.url)      

        # Проверяем расширение файла
        if not file.filename.lower().endswith('.csv'):
            logger.warning(f'Загружен файл абонентов с неправильным расширением: {file.filename}')
            flash('Поддерживаются только CSV-файлы','warning')
            return redirect(request.url)

        # Получаем путь к временному файлу
        filepath = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(filepath)

        logger.info(f'загружен файл абонентов: {filepath}')

        # Чтение данных из загруженного CSV-файла
        try:
            with get_session() as session:
                with open(filepath, mode='r', encoding='utf-8') as csvfile:
                    # Чтение данных из загруженного CSV-файла
                    reader = csv.reader(csvfile)
                    next(reader)  # Пропускаем первую строку (заголовки)
    
                    for row in reader:
                        # Парсим данные из каждой строки
                        try:
                            phone, department, username, fio, _, password = row
                        except ValueError:
                            continue  # Пропускаем строки с неверной структурой

                        if phone:
                            phone = phone.strip()
                            phone = int(phone)

                        # если задан пароль, то удяляем лишние пробелы
                        if password:
                            password = password.strip()

                        existing_auth = session.get(PJSIPAuth, phone)
                        if existing_auth:
                            existing_auth.username = username
                            # если пароль задан и не пустой, то обновляем пароль
                            if password:
                                existing_auth.set_password(password.strip())
                        else:
                            if password:
                                new_auth = PJSIPAuth(
                                    id=phone,
                                    username=username)
                                new_auth.set_password(password.strip())
                                session.add(new_auth)
                            else:
                                logger.warning(f'Для нового абонента не задан пароль: {username}')
                                flash(f'Для нового абонента не задан пароль: {username}', 'danger')
                                return redirect(request.url)

                        existing_aor = session.get(PJSIPAor, phone)
                        if not existing_aor:
                            new_aor = PJSIPAor(id=phone)
                            session.add(new_aor)

                        # Проверяем, существует ли пользователь с таким именем
                        existing_exten = session.get(PJSIPEndpoint, phone)
                        if existing_exten:
                            # Обновляем данные существующего пользователя
                            existing_exten.department = department
                            existing_exten.fio = fio
                            existing_exten.aors = phone
                            existing_exten.auth = phone                            
                        else:                            
                            new_exten = PJSIPEndpoint(
                                id=phone,
                                department=department,
                                fio=fio,
                                aors=phone,
                                auth=phone
                            )
                            session.add(new_exten)
                        


                # Сохраняем изменения в базу данных
                session.commit()
                
                # Удалим все записи старше upload_time кроме admin
                session.query(PJSIPEndpoint).filter(PJSIPEndpoint.updated_at < func.now()).delete()
                
                session.commit()

            flash('Данные успешно загружены!', 'success')
            return redirect(url_for('extens_bp.show_extens'))

        except Exception as e:
            flash(f'Ошибка при обработке файла: {e}', 'danger')
            logger.error(f'Ошибка при обработке файла: {e}')
            return redirect(request.url)

        finally:
            # Удаляем файл после обработки
            os.remove(filepath)

    else:
        return render_template('extens_upload_file.html')
