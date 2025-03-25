import os
from dotenv import load_dotenv
import logging
from flask import (
    Flask, render_template, request, redirect, url_for, flash
)
from flask_login import (
    LoginManager, login_user, logout_user, current_user, login_required
)
from sqlalchemy import desc

# Импортируем модели из models.py
from models import User, Calls, db

load_dotenv()

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Настройка логирования
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app_client")

# Читаем переменные из .env
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))  # Порт преобразуем в целое число
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Формируем URI для SQLAlchemy
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем DB
db.init_app(app)

# Инициализируем LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return render_template('holl.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Неправильное имя пользователя или пароль.')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fio = request.form['fio']
        phone = request.form['phone']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Имя пользователя уже занято.')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            fio=fio,
            phone=phone
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Аккаунт успешно создан!')
        return redirect(url_for('login'))

    return render_template('register.html')


from datetime import datetime, timedelta
import re

@app.route('/calls/history')
@login_required
def history():
    # Установка значений by default
    date_time_format = '%Y-%m-%d'   # формат DD.MM.YY
    limit = 10
    today = datetime.now().strftime(date_time_format)  # Текущая дата в формате DD.MM.YYYY
    page = request.args.get('page', 1)
    fromdt = request.args.get('fromdt', today)
    todt = request.args.get('todt', today)

    # Преобразование строковых значений в объекты datetime
    try:
        from_date = datetime.strptime(fromdt, date_time_format)
        to_date = datetime.strptime(todt, date_time_format) + timedelta(days=1)
        
    except ValueError:
        # Если дата некорректна, возвращаем ошибку
        flash(f'Некорректный формат даты. Должен быть YYYY-MM-DD.')
        return redirect(url_for('history'))

    # Определяем базовый запрос
    base_query = Calls.query.order_by(desc(Calls.call_start))

    # Применяем фильтры по дате
    if from_date:
        base_query = base_query.filter(Calls.call_start >= from_date)
    if to_date:
        base_query = base_query.filter(Calls.call_start <= to_date)
  
    # Извлекаем записи для текущей страницы
    paginate = base_query.paginate(page=page, per_page=limit, error_out=False)

    # Формируем контекст для рендеринга
    context = {
        'pagination': paginate,
        'fromdt': fromdt,
        'todt': todt
    }

    return render_template('history.html', **context)


@app.route('/users')
@login_required
def show_users():
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

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    # Получаем список существующих отделов
    existing_departments = db.session.query(User.department).distinct().all()

    if request.method == 'POST':
        # Получаем данные из формы
        department = request.form['new_department'] or request.form['existing_department']
        username = request.form['username']
        fio = request.form['fio']
        phone = request.form['phone']
        password = request.form['password'].strip()

        # Создаем нового пользователя
        user = User(username=username, fio=fio, phone=phone, department=department)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан!', 'success')
            return redirect(url_for('show_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {e}', 'danger')

    return render_template('user_edit.html', user=None, existing_departments=existing_departments)

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
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
        return redirect(url_for('show_users'))
    
    return render_template('user_edit.html', user=user, existing_departments=existing_departments)

@app.route('/users/delete/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    """
    Обработчик для удаления пользователя.
    """
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(user)
            db.session.commit()
            flash('Пользователь успешно удален.', 'success')
            return redirect(url_for('show_users'))  # Переходим на список пользователей
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при удалении пользователя: {e}', 'error')
            logger.error(f'Error deleting user with id={id}: {e}')
    return render_template('user_delete_confirm.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)