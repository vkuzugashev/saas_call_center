import os
from dotenv import load_dotenv
import logging
from flask import (
    Flask, request, render_template, redirect, url_for, flash
)
from flask_login import (
    LoginManager, current_user, login_user, logout_user, login_required
)
from pages.settings import settings_bp
from pages.call_categories import categories_bp
from pages.users import users_bp
from pages.call_log import call_log_bp
from pages.contacts import contacts_bp

# Импортируем модели из models.py
from models import db, User

load_dotenv()

# Настройки сервера
DEBUG = bool(os.getenv('DEBUG', True))

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Настройка логирования
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app_client")

# Читаем переменные из .env
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))  # Порт преобразуем в целое число
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PWD = os.getenv('DB_PWD')
DB_NAME = os.getenv('DB_NAME')

# Формируем URI для SQLAlchemy
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки пользователя администратора
app.config['MANAGER_USER'] = os.getenv('MANAGER_USER')


# Инициализируем DB
db.init_app(app)

# Инициализируем LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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
    return User.query.get(int(user_id))

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
       

       user = User.query.filter_by(username=username).first()

       if user is not None and user.check_password(password):
           logger.debug(f'Logging username: {username}, password: {password}')
           login_user(user)
           logger.debug(f'Logged username: {username}, password: {password}')
           return redirect(url_for('index'))

       flash('Неправильное имя пользователя или пароль.')

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


# Регистрируем маршруты из других модулей
app.register_blueprint(settings_bp)
app.register_blueprint(users_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(call_log_bp)
app.register_blueprint(contacts_bp)

if __name__ == '__main__':
    app.config['modules'] = get_modules_settings()
    app.run( host='0.0.0.0', port=5000, debug=DEBUG)