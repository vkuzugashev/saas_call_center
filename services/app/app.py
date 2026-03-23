import os
from dotenv import load_dotenv
import logging
from flask import (
    Flask, request, render_template, redirect, url_for, flash
)
from flask_login import (
    LoginManager, current_user, login_user, logout_user, login_required
)
from sqlalchemy import select

from pages.settings import settings_bp
from pages.call_categories import categories_bp
from pages.users import users_bp
from pages.extens import extens_bp
from pages.call_log import call_log_bp
from pages.contacts import contacts_bp
from pages.report import report_bp

from sqlalchemy.orm import Session

# Импортируем модели из models.py
from models.model import User, get_db, init_db

load_dotenv()

# Настройки сервера
APP_FLASK_DEBUG = bool(os.getenv('APP_FLASK_DEBUG', True))

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Настройка логирования
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app_client")

# Читаем переменные из .env
LISTEN_HOST = os.getenv('APP_LISTEN_HOST')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')
# Настройки пользователя администратора
app.config['MANAGER_USER'] = os.getenv('APP_MANAGER_USER')
app.config['MANAGEMENT_CONSOLE_URL'] = os.getenv('APP_MANAGEMENT_CONSOLE_URL')

# Инициализируем LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Получение сессии
def get_session() -> Session:
    return next(get_db())

def get_modules_settings():
    modules = {}
    modules['MOD_STATISTIC'] = os.environ.get('MOD_STATISTIC', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    modules['MOD_RECORD'] = os.environ.get('MOD_RECORD', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    modules['MOD_TRANSCRIPT'] = os.environ.get('MOD_TRANSCRIPT', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    modules['MOD_NEW_CALL'] = os.environ.get('MOD_NEW_CALL', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    print(modules)
    return modules

@login_manager.user_loader
def load_user(user_id):
    with get_session() as session:
        return session.get(User, int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html', modules = app.config['modules'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обработчик для входа пользователя в систему.

    Returns:
       Response: Ответ сервера.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
       
        with get_session() as session:
            user = session.execute(
                select(User)
                .where(User.username == username)
            ).scalar_one_or_none()

            if user and user.check_password(password):
                logger.debug(f'Logging username: {username}, password: {password}')
                login_user(user)
                logger.debug(f'Logged username: {username}, password: {password}')
                return redirect(url_for('index'))

        flash('Неправильное имя пользователя или пароль.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """
    Обработчик для выхода пользователя из системы.

    Returns:
        Response: Ответ сервера.
    """
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Обработчик для регистрации нового пользователя.

    Returns:
        Response: Ответ сервера.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fio = request.form['fio']
        phone = request.form['phone']

        with get_session() as session:
            existing_user = session.execute(
                select(User)
                .where(User.username == username)
            ).scalar_one_or_none()

            if existing_user:
                flash('Имя пользователя уже занято.', 'danger')
                return redirect(url_for('register'))

            new_user = User(
                username=username,
                fio=fio,
                phone=phone
            )
            new_user.set_password(password)
            session.add(new_user)
            session.commit()

        flash('Аккаунт успешно создан!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Регистрируем маршруты из других модулей
app.register_blueprint(settings_bp)
app.register_blueprint(users_bp)
app.register_blueprint(extens_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(call_log_bp)
app.register_blueprint(contacts_bp)
app.register_blueprint(report_bp)


if __name__ == '__main__':
    init_db()
    app.config['modules'] = get_modules_settings()
    app.run(host=LISTEN_HOST, port=5000, debug=APP_FLASK_DEBUG)