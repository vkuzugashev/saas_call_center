import os
from dotenv import load_dotenv
import logging
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, current_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash

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


@app.route('/calls/history', defaults={'page': 1})
@app.route('/calls/history/page/<int:page>')
@login_required
def history(page):
    calls_per_page = 10
    pagination = Calls.query.order_by(Calls.call_start.desc()).paginate(
        page, per_page=calls_per_page, error_out=False
    )
    calls = pagination.items
    return render_template(
        'call_history.html',
        calls=calls,
        pagination=pagination
    )


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