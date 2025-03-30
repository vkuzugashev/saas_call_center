import csv
from io import StringIO
import logging
import os
import tempfile
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import db, User

users_bp = Blueprint('users_bp', __name__, template_folder='../templates/users')

logger = logging.getLogger("users")

@users_bp.route('/users')
@login_required
def show_users():
   """
   Обработчик для отображения списка пользователей.

   Returns:
       Response: Ответ сервера.
   """
   departments = db.session.query(User.department).distinct().all()
   selected_department = request.args.get('department')

   if selected_department:
       users = User.query.filter_by(department=selected_department).all()
   else:
       users = User.query.all()

   return render_template(
       'users.html',
       users=users,
       departments=departments,
       selected_department=selected_department
   )


@users_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
   """
   Обработчик для создания нового пользователя.

   Returns:
       Response: Ответ сервера.
   """
   # Получаем список существующих отделов
   existing_departments = db.session.query(User.department).distinct().all()

   if request.method == 'POST':
       # Получаем данные из формы
       department = request.form['new_department'] or request.form['existing_department']
       username = request.form['username']
       fio = request.form['fio']
       phone = request.form['phone']
       password = request.form['password'].strip()

       if not password:
           flash('Пароль не может быть пустым.', 'danger')
           return redirect(url_for('users_bp.show_users'))
       
       # Создаем нового пользователя
       user = User(username=username, fio=fio, phone=phone, department=department)
       user.set_password(password)

       try:
           db.session.add(user)
           db.session.commit()
           flash(f'Пользователь [{user.username}] успешно создан!', 'success')
           return redirect(url_for('users_bp.show_users'))
       except Exception as e:
           db.session.rollback()
           flash(f'Ошибка при создании пользователя [{user.username}]: {e}', 'danger')

   return render_template('user_edit.html', user=None, existing_departments=existing_departments)


@users_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
   """
   Обработчик для редактирования пользователя.

   Args:
       id (int): Идентификатор пользователя, которого нужно редактировать.

   Returns:
       Response: Ответ сервера.
   """
   user = User.query.get_or_404(id)
   
   # Получаем список существующих отделов
   existing_departments = db.session.query(User.department).distinct().all()
   logger.debug('Departmets:', existing_departments)

   if request.method == 'POST':
       # Получаем данные из формы
       department = request.form['new_department'] or request.form['existing_department']
       user.department = department
       user.fio = request.form['fio']
       user.phone = request.form['phone']
       password = request.form['password'].strip()
       
       # Проверяем, если пароль введен и не пустая строка
       if password:
           user.set_password(password)
           
       db.session.commit()
       
       flash(f'Пользователь [{user.username}] успешно обновлен!', 'success')
       return redirect(url_for('users_bp.show_users'))
   
   return render_template('user_edit.html', user=user, existing_departments=existing_departments)


@users_bp.route('/users/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    """
    Обработчик для удаления пользователя.

    Args:
       id (int): Идентификатор пользователя, которого нужно удалить.

    Returns:
       Response: Ответ сервера.
    """
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        if current_user.id == user.id:
            flash('Вы не можете удалить самого себя.', 'danger')
            return redirect(url_for('users_bp.show_users'))
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f'Пользователь [{user.username}] успешно удален.', 'success')
            return redirect(url_for('users_bp.show_users'))  # Переходим на список пользователей
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при удалении пользователя: [{user.username}], {e}', 'danger')
            logger.error(f'Error deleting user with id={id}: {e}')
    return render_template('user_delete_confirm.html', user=user)


@users_bp.route('/users/export_csv')
@login_required
def users_export_csv():
   """
   Обработчик для экспорта пользователей в CSV-файл.

   Returns:
       Response: Ответ сервера.
   """
   # Получаем всех пользователей
   users = User.query.all()
   
   # Создаем строку для хранения CSV-данных
   si = StringIO()
   cw = csv.writer(si)
   
   # Заголовки столбцов
   cw.writerow(['ID', 'Отдел', 'Имя пользователя', 'ФИО', 'Телефон', 'Пароль'])
   
   # Заполняем строки данными
   for user in users:
       cw.writerow([user.id, user.department, user.username, user.fio, user.phone, None])
   
   # Преобразуем содержимое StringIO в байты
   output = make_response(si.getvalue())
   
   # Устанавливаем заголовок Content-Disposition для скачивания файла
   output.headers["Content-Disposition"] = "attachment; filename=users.csv"
   output.headers["Content-type"] = "text/csv"
   
   return output


@users_bp.route('/users/upload_csv', methods=['GET', 'POST'])
@login_required
def users_upload_csv():
   """
   Обработчик для загрузки пользователей из CSV-файла.

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
           logger.warning(f'Загружен файл пользователей с неправильным расширением: {filepath}')
           flash('Поддерживаются только CSV-файлы','warning')
           return redirect(request.url)

       # Получаем путь к временному файлу
       filepath = os.path.join(tempfile.gettempdir(), file.filename)
       file.save(filepath)

       logger.info(f'загружен файл пользователей: {filepath}')

       # Чтение данных из загруженного CSV-файла
       try:
           with open(filepath, mode='r', encoding='utf-8') as csvfile:
               # Чтение данных из загруженного CSV-файла
               reader = csv.reader(csvfile)
               next(reader)  # Пропускаем первую строку (заголовки)

               for row in reader:
                   # Парсим данные из каждой строки
                   try:
                       _, department, username, fio, phone, password = row
                   except ValueError:
                       continue  # Пропускаем строки с неверной структурой

                   # Проверяем, существует ли пользователь с таким именем
                   existing_user = User.query.filter_by(username=username).first()
                   
                   # если задан пароль, то удяляем лишние пробелы
                   if password:
                       password = password.strip()

                   if existing_user:
                       # Обновляем данные существующего пользователя
                       existing_user.department = department
                       existing_user.fio = fio
                       existing_user.phone = phone                        
                       # если пароль не задан оставляем прежний
                       if password:
                           existing_user.set_password(password.strip())
                   else:
                       # Создаем нового пользователя
                       if not password:
                           logger.warning(f'Для нового пользователя не задан пароль: {username}')
                           flash(f'Для нового пользователя не задан пароль: {username}', 'danger')
                           return redirect(request.url)
                       
                       new_user = User(
                           department=department,
                           username=username,
                           fio=fio,
                           phone=phone
                       )
                       new_user.set_password(password)

                       db.session.add(new_user)

               # Сохраняем изменения в базу данных
               db.session.commit()

           flash('Данные успешно загружены!')
           return redirect(url_for('users_bp.show_users'))

       except Exception as e:
           flash(f'Ошибка при обработке файла: {e}', 'danger')
           logger.error(f'Ошибка при обработке файла: {e}')
           return redirect(request.url)

       finally:
           # Удаляем файл после обработки
           os.remove(filepath)

   else:
       return render_template('users_upload_file.html')
